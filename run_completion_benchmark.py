
import os
import sys
import time
import json
import yaml
import subprocess
import glob
import argparse
import importlib.util
import threading
from datetime import datetime
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
RESULTS_FILE = "completion_benchmark.json"
LOGS_DIR = "logs"

SCORE_THRESHOLD = 1.0  # Only run OpenEvolve if Gemma scores below this
DEFAULT_ITERATION_LIMIT = 300  # Iteration limit for OpenEvolve completion benchmark
DEFAULT_PATIENCE = 100  # Early stopping patience if no improvement
BASELINE_TIMEOUT = 120  # Timeout in seconds for baseline Gemma generation


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
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": "Please implement the module described above. Output ONLY the Verilog code."}
    ]

    # Use a thread with timeout to prevent hanging on complex problems
    result_container = [None]
    error_container = [None]

    def generate():
        try:
            result_container[0] = llm.create_chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=4096
            )
        except Exception as e:
            error_container[0] = e

    thread = threading.Thread(target=generate)
    thread.start()
    thread.join(timeout=BASELINE_TIMEOUT)

    if thread.is_alive():
        print(f"  WARNING: Gemma generation timed out after {BASELINE_TIMEOUT}s")
        return {
            "score": 0.0, "accuracy": 0.0,
            "time": time.time() - start_time,
            "mode": "pure_gemma_timeout"
        }
    if error_container[0]:
        raise error_container[0]

    response = result_container[0]

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


def run_openevolve(problem_dir: str, config_path: str, max_iterations: int = 300,
                   patience: int = 100, jumpstart_path: str = None, prob_name: str = "unknown") -> Dict[str, Any]:
    """Runs OpenEvolve via subprocess with iteration limit and early stopping."""
    start_time = time.time()

    # Create a temporary config
    config = load_config(config_path)
    config['target_score'] = 1.0  # Stop if perfect
    config['early_stopping_patience'] = patience

    temp_config_path = os.path.join(problem_dir, "gemma_config_benchmark.yaml")
    with open(temp_config_path, 'w') as f:
        yaml.dump(config, f)

    if jumpstart_path and os.path.exists(jumpstart_path):
        initial_program = jumpstart_path
        print(f"  Jump-starting OpenEvolve with baseline code: {initial_program}")
    else:
        initial_program = os.path.join(problem_dir, "initial_program.v")

    evaluator_script = os.path.join(problem_dir, "evaluator.py")

    cmd = [
        sys.executable, "-m", "openevolve.cli",
        initial_program,
        evaluator_script,
        "--config", temp_config_path,
        "--iterations", str(max_iterations),  # Stop precisely at this iteration limit
        "--log-level", "DEBUG"  # Full debug logging to file
    ]

    # Create timestamped log file
    os.makedirs(LOGS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(LOGS_DIR, f"completion_{prob_name}_{timestamp}.log")
    print(f"  Logging DEBUG output to: {log_filename}")

    # Run process, streaming all output to the log file
    try:
        with open(log_filename, "w") as logfile:
            logfile.write(f"=== Completion Benchmark - OpenEvolve Log ===\n")
            logfile.write(f"Problem: {prob_name}\n")
            logfile.write(f"Timestamp: {timestamp}\n")
            logfile.write(f"Initial Program: {initial_program}\n")
            logfile.write(f"Config: {temp_config_path}\n")
            logfile.write(f"Iteration Limit: {max_iterations}\n")
            logfile.write(f"Patience: {patience}\n")
            logfile.write(f"Command: {' '.join(cmd)}\n")
            logfile.write(f"{'=' * 60}\n\n")
            logfile.flush()
            result = subprocess.run(cmd, check=True, stdout=logfile, stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
        print(f"  OpenEvolve failed with exit code {e.returncode}")
        print(f"  Check log file for details: {log_filename}")
        return {"score": 0.0, "accuracy": 0.0, "time": 0.0, "mode": "openevolve_error", "log": log_filename}
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)

    execution_time = time.time() - start_time

    # Read best result from output dir
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
                "mode": "openevolve",
                "log": log_filename
            }

    return {"score": 0.0, "accuracy": 0.0, "time": execution_time, "mode": "openevolve_failed_read", "log": log_filename}


def main():
    parser = argparse.ArgumentParser(description="Completion Benchmark: OpenEvolve vs Native Gemma")
    parser.add_argument("--limit", type=int, default=0, help="Number of problems to run (0 = all)")
    parser.add_argument("--max-iterations", type=int, default=DEFAULT_ITERATION_LIMIT,
                        help=f"OpenEvolve max iterations / checkpoint limit (default: {DEFAULT_ITERATION_LIMIT})")
    parser.add_argument("--patience", type=int, default=DEFAULT_PATIENCE,
                        help=f"OpenEvolve early stopping patience (default: {DEFAULT_PATIENCE})")
    parser.add_argument("--jumpstart", action="store_true", default=False,
                        help="Use native Gemma baseline output as initial program for OpenEvolve (default: disabled)")
    parser.add_argument("--start", type=int, default=1,
                        help="Problem number to start from (1-indexed, default: 1). Previous results are preserved.")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for LLM generation (default: 42)")
    args = parser.parse_args()

    if not os.path.exists(DATASET_DIR):
        print(f"Error: Dataset {DATASET_DIR} not found.")
        return

    # We will lazy-load the baseline LLM to allow freeing memory for OpenEvolve
    llm = None

    problems = sorted(glob.glob(os.path.join(DATASET_DIR, "Prob*")))
    total_problems = len(problems) if args.limit == 0 else min(len(problems), args.limit)
    results = []

    # Counters for summary
    gemma_solved = 0
    gemma_failed = 0
    openevolve_attempted = 0
    openevolve_solved = 0

    # Resume support: load existing results and reconstruct counters
    start_idx = args.start - 1  # Convert 1-indexed to 0-indexed
    if start_idx > 0 and os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r') as f:
            existing_results = json.load(f)
        # Keep results up to (but not including) the start index
        results = existing_results[:start_idx]
        # Reconstruct counters from loaded results
        for r in results:
            if r.get("gemma_solved", False):
                gemma_solved += 1
            else:
                gemma_failed += 1
                oe = r.get("openevolve", {})
                if isinstance(oe, dict):
                    openevolve_attempted += 1
                    if r.get("openevolve_solved", False):
                        openevolve_solved += 1
        print(f"  Resuming from problem {args.start}. Loaded {len(results)} previous results.")

    print(f"\n{'=' * 70}")
    print(f"  COMPLETION BENCHMARK")
    print(f"  Problems: {total_problems} | Iteration Limit: {args.max_iterations} | Patience: {args.patience}")
    print(f"  Strategy: Run OpenEvolve ONLY when Gemma scores < {SCORE_THRESHOLD}")
    if start_idx > 0:
        print(f"  Resuming from: Problem {args.start}")
    print(f"{'=' * 70}\n")

    for i, problem_dir in enumerate(problems):
        if args.limit > 0 and i >= args.limit:
            break
        if i < start_idx:
            continue

        prob_name = os.path.basename(problem_dir)
        config_path = os.path.join(problem_dir, "gemma_config.yaml")

        print(f"\n[{i+1}/{total_problems}] --- {prob_name} ---")

        # 1. Pure Gemma Baseline
        print(f"  Running Native Gemma...")
        try:
            if llm is None:
                print("  Loading Gemma model for Baseline...")
                llm = Llama(
                    model_path=DEFAULT_MODEL_PATH,
                    n_ctx=8192,
                    n_gpu_layers=-1,  # GPU for fast inference
                    seed=args.seed,
                    verbose=False
                )
            baseline_res = run_pure_gemma(llm, problem_dir, config_path)
        except Exception as e:
            print(f"  ERROR running Gemma: {e}")
            baseline_res = {"score": 0.0, "accuracy": 0.0, "time": 0.0, "mode": "pure_gemma_error"}
        print(f"  Gemma Score: {baseline_res['score']:.4f} (accuracy={baseline_res.get('accuracy', 0):.4f})")

        entry = {
            "problem": prob_name,
            "baseline": baseline_res,
        }

        # 2. Check if Gemma already solved it
        if baseline_res['score'] >= SCORE_THRESHOLD:
            gemma_solved += 1
            entry["openevolve"] = "skipped"
            entry["gemma_solved"] = True
            print(f"  ✓ Gemma solved it (score >= {SCORE_THRESHOLD}). Skipping OpenEvolve.")
        else:
            gemma_failed += 1
            openevolve_attempted += 1
            print(f"  ✗ Gemma failed (score < {SCORE_THRESHOLD}). Running OpenEvolve (iterations={args.max_iterations}, patience={args.patience})...")

            # Free up baseline LLM VRAM before spawning OpenEvolve
            if llm is not None:
                del llm
                import gc
                gc.collect()
                llm = None

            jumpstart_code = baseline_res.get('code_path') if args.jumpstart else None
            try:
                evolve_res = run_openevolve(
                    problem_dir, config_path, args.max_iterations, args.patience,
                    jumpstart_path=jumpstart_code, prob_name=prob_name
                )
                print(f"  OpenEvolve Score: {evolve_res['score']:.4f} (accuracy={evolve_res.get('accuracy', 0):.4f}, time={evolve_res['time']:.1f}s)")

                entry["openevolve"] = evolve_res
                entry["gemma_solved"] = False
                entry["openevolve_solved"] = evolve_res['score'] >= SCORE_THRESHOLD

                if evolve_res['score'] >= SCORE_THRESHOLD:
                    openevolve_solved += 1
                    print(f"  ✓ OpenEvolve COMPLETED the problem!")
                else:
                    print(f"  ✗ OpenEvolve could not fully solve it either.")
            except Exception as e:
                print(f"  ERROR running OpenEvolve: {e}")
                entry["openevolve"] = {"score": 0.0, "accuracy": 0.0, "time": 0.0, "mode": "openevolve_error"}
                entry["gemma_solved"] = False
                entry["openevolve_solved"] = False

        results.append(entry)

        # Save incrementally (in case of crash)
        with open(RESULTS_FILE, 'w') as f:
            json.dump(results, f, indent=2)

    # Final Summary
    print(f"\n{'=' * 70}")
    print(f"  COMPLETION BENCHMARK RESULTS")
    print(f"{'=' * 70}")
    print(f"  Total problems tested:          {len(results)}")
    print(f"  Gemma solved (score >= 1.0):     {gemma_solved}")
    print(f"  Gemma failed (score <  1.0):     {gemma_failed}")
    print(f"  OpenEvolve attempted:            {openevolve_attempted}")
    print(f"  OpenEvolve solved:               {openevolve_solved}")
    if openevolve_attempted > 0:
        print(f"  OpenEvolve completion rate:      {openevolve_solved}/{openevolve_attempted} ({100*openevolve_solved/openevolve_attempted:.1f}%)")
    print(f"{'=' * 70}")

    # Detailed table for failed problems
    failed_entries = [r for r in results if not r.get("gemma_solved", False)]
    if failed_entries:
        print(f"\n--- Detailed Results: Problems Gemma Could NOT Solve ---")
        print(f"{'Problem':<25} | {'Gemma':>8} | {'OpenEvolve':>10} | {'Completed?':>10}")
        print("-" * 65)
        for entry in failed_entries:
            gemma_score = entry['baseline']['score']
            oe = entry.get('openevolve', {})
            if isinstance(oe, dict):
                oe_score = oe.get('score', 0.0)
                completed = "YES" if entry.get('openevolve_solved', False) else "NO"
            else:
                oe_score = 0.0
                completed = "N/A"
            print(f"{entry['problem']:<25} | {gemma_score:>8.4f} | {oe_score:>10.4f} | {completed:>10}")

    print(f"\nResults saved to {RESULTS_FILE}")


if __name__ == "__main__":
    main()
