
import os
import sys
import time
import json
import yaml
import subprocess
import glob
import argparse
import importlib.util
from typing import Dict, Any, List

# Try to import llama_cpp
try:
    from llama_cpp import Llama
except ImportError:
    print("Warning: llama-cpp-python not found. Pure Gemma baseline will fail if attempted.")
    Llama = None

# Configuration defaults
DEFAULT_MODEL_PATH = "/home/jonathan13/GemmaEvolve/gemma-3-12b-it-Q8_0.gguf"
DATASET_DIR = "examples/verilog_eval"
RESULTS_FILE = "benchmark_results.json"

def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def run_pure_gemma(llm, problem_dir: str, config_path: str) -> Dict[str, Any]:
    """Runs a zero-shot attempt using the raw Gemma model."""
    start_time = time.time()
    
    # Load config to get the prompt
    config = load_config(config_path)
    system_msg = config['prompt']['system_message']
    
    # Construct a simple zero-shot prompt
    # We assume 'system_message' contains the problem description and interface
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": "Please implement the module described above. Output ONLY the Verilog code."}
    ]
    
    response = llm.create_chat_completion(
        messages=messages,
        temperature=0.7,
        max_tokens=4096
    )
    
    generated_code = response["choices"][0]["message"]["content"]
    
    # Extract code if wrapped in markdown
    if "```verilog" in generated_code:
        generated_code = generated_code.split("```verilog")[1].split("```")[0].strip()
    elif "```" in generated_code:
        generated_code = generated_code.split("```")[1].split("```")[0].strip()
        
    execution_time = time.time() - start_time
    
    # Evaluate
    evaluator_path = os.path.join(problem_dir, "evaluator.py")
    spec = importlib.util.spec_from_file_location("evaluator", evaluator_path)
    evaluator_module = importlib.util.module_from_spec(spec)
    sys.modules["evaluator"] = evaluator_module
    spec.loader.exec_module(evaluator_module)
    
    # Run evaluation inside the problem directory to resolve relative paths (testbench.sv)
    original_cwd = os.getcwd()
    os.chdir(problem_dir)
    try:
        result = evaluator_module.evaluate(generated_code)
    finally:
        os.chdir(original_cwd)
        
    # Save baseline generated code
    code_path = os.path.join(problem_dir, "baseline_generated.v")
    with open(code_path, "w") as f:
        f.write(generated_code)

    return {
        "score": result.get("combined_score", 0.0),
        "accuracy": result.get("accuracy", 0.0),
        "time": execution_time,
        "mode": "pure_gemma",
        "code_path": code_path
    }

def run_openevolve(problem_dir: str, config_path: str, patience: int = 30, jumpstart_path: str = None) -> Dict[str, Any]:
    """Runs OpenEvolve via subprocess with early stopping."""
    start_time = time.time()
    
    # Create a temporary config with early stopping injection
    config = load_config(config_path)
    config['early_stopping_patience'] = patience
    config['target_score'] = 1.0 # Stop if perfect
    
    # Adjust for speed: single island if possible for quick benchmarking? 
    # Or keep default but rely on patience.
    
    temp_config_path = os.path.join(problem_dir, "gemma_config_benchmark.yaml")
    with open(temp_config_path, 'w') as f:
        yaml.dump(config, f)
        
    if jumpstart_path and os.path.exists(jumpstart_path):
        initial_program = jumpstart_path
        print(f"Jump-starting OpenEvolve with baseline code: {initial_program}")
    else:
        initial_program = os.path.join(problem_dir, "initial_program.v")
        
    evaluator_script = os.path.join(problem_dir, "evaluator.py")
    
    cmd = [
        sys.executable, "-m", "openevolve.cli",
        initial_program,
        evaluator_script,
        "--config", temp_config_path,
        "--iterations", "50", # Max iterations
        "--log-level", "WARNING" # Reduce spam
    ]
    
    # Run process
    try:
        # Capture output to parse the final result if needed
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"OpenEvolve failed with exit code {e.returncode}")
        print(f"STDOUT:\n{e.stdout}")
        print(f"STDERR:\n{e.stderr}")
        return {"score": 0.0, "accuracy": 0.0, "time": 0.0, "mode": "openevolve_error"}
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)
            
    execution_time = time.time() - start_time
    
    # Read best result from output dir
    # openevolve_output is adjacent to initial_program.v
    output_dir = os.path.join(problem_dir, "openevolve_output")
    best_info_path = os.path.join(output_dir, "best", "best_program_info.json")
    
    if os.path.exists(best_info_path):
        with open(best_info_path, 'r') as f:
            info = json.load(f)
            metrics = info.get("metrics", {})
            return {
                "score": metrics.get("combined_score", 0.0),
                "accuracy": metrics.get("accuracy", 0.0),
                "time": execution_time,
                "mode": "openevolve"
            }
    
    return {"score": 0.0, "accuracy": 0.0, "time": execution_time, "mode": "openevolve_failed_read"}

def main():
    parser = argparse.ArgumentParser(description="Benchmark Pure Gemma vs OpenEvolve")
    parser.add_argument("--limit", type=int, default=3, help="Number of problems to run")
    parser.add_argument("--patience", type=int, default=30, help="OpenEvolve early stopping patience")
    args = parser.parse_args()
    
    if not os.path.exists(DATASET_DIR):
        print(f"Error: Dataset {DATASET_DIR} not found.")
        return

    # Initialize LLM for Pure Baseline
    print("Loading Gemma model for Baseline...")
    llm = Llama(
        model_path=DEFAULT_MODEL_PATH,
        n_ctx=8192,
        n_gpu_layers=0, # CPU only for stability during benchmark
        verbose=False
    )
    
    problems = sorted(glob.glob(os.path.join(DATASET_DIR, "Prob*")))
    results = []
    
    print(f"Running benchmark on {min(len(problems), args.limit)} problems...")
    
    for i, problem_dir in enumerate(problems):
        if i >= args.limit:
            break
            
        prob_name = os.path.basename(problem_dir)
        config_path = os.path.join(problem_dir, "gemma_config.yaml")
        
        print(f"\n--- Benchmarking {prob_name} ---")
        
        # 1. Pure Gemma Baseline
        print(f"Running Pure Gemma Baseline...")
        baseline_res = run_pure_gemma(llm, problem_dir, config_path)
        print(f"  Result: Score={baseline_res['score']:.4f}, Time={baseline_res['time']:.2f}s")
        
        # 2. OpenEvolve
        print(f"Running OpenEvolve (Patience={args.patience})...")
        jumpstart_code = baseline_res.get('code_path')
        evolve_res = run_openevolve(problem_dir, config_path, args.patience, jumpstart_path=jumpstart_code)
        print(f"  Result: Score={evolve_res['score']:.4f}, Time={evolve_res['time']:.2f}s")
        
        results.append({
            "problem": prob_name,
            "baseline": baseline_res,
            "openevolve": evolve_res
        })
        
    # Save results
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"\nBenchmark complete. Results saved to {RESULTS_FILE}")
    
    # Simple ASCII Chart
    print("\n--- Comparative Analysis ---")
    print(f"{'Problem':<20} | {'Baseline':<10} | {'OpenEvolve':<10} | {'Time (Base vs Evo)':<20}")
    print("-" * 70)
    for res in results:
        base_score = res['baseline']['score']
        evo_score = res['openevolve']['score']
        base_time = res['baseline']['time']
        evo_time = res['openevolve']['time']
        
        print(f"{res['problem']:<20} | {base_score:.4f}     | {evo_score:.4f}     | {base_time:6.2f}s / {evo_time:6.2f}s")

if __name__ == "__main__":
    main()
