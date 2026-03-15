
import os
import shutil
import re
import glob

# Configuration
SOURCE_DIR = 'verilog-eval/dataset_code-complete-iccad2023'
DEST_DIR = 'examples/verilog_eval'
TEMPLATE_MODEL_PATH = "/home/jonathan13/GemmaEvolve/gemma-3-12b-it-Q8_0.gguf"

EVALUATOR_TEMPLATE = """import os
import subprocess
import re
import tempfile
import logging

logger = logging.getLogger(__name__)

def evaluate(code: str) -> dict:
    "Evaluate Verilog code using Icarus Verilog."
    # If the input is a file path, read the code from it
    if os.path.exists(code) and os.path.isfile(code):
        with open(code, 'r') as f:
            code = f.read()

    # Write code to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.v', prefix='verilog_eval_', delete=False) as f:
        f.write(code)
        candidate_path = f.name
    
    # Path to testbench (relative to project root)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    testbench_path = os.path.join(script_dir, "testbench.sv")
    reference_path = os.path.join(script_dir, "ref.sv")
    executable_path = candidate_path + ".out"
    
    try:
        # Compile using iverilog
        # iverilog -g2012 -o <exec> <candidate> <testbench> <reference>
        compile_cmd = ["iverilog", "-g2012", "-o", executable_path, candidate_path, testbench_path, reference_path]
        try:
            subprocess.check_output(compile_cmd, stderr=subprocess.STDOUT, timeout=10)
        except subprocess.CalledProcessError as e:
            error_msg = e.output.decode()
            logger.warning(f"Compilation failed: {error_msg}")
            return {"combined_score": 0.0, "accuracy": 0.0, "error": f"Compilation failed: {error_msg}"}
        
        # Run simulation using vvp
        run_cmd = ["vvp", executable_path]
        try:
            output = subprocess.check_output(run_cmd, stderr=subprocess.STDOUT, timeout=10).decode()
        except subprocess.CalledProcessError as e:
            error_msg = e.output.decode()
            if "TIMEOUT" in error_msg:
                 return {"combined_score": 0.0, "accuracy": 0.0, "error": "Simulation Timeout"}
            
            logger.warning(f"Runtime error: {error_msg}")
            return {"combined_score": 0.0, "accuracy": 0.0, "error": f"Runtime error: {error_msg}"}
        
        # Parse output for mismatches
        accuracy = 0.0
        match = re.search(r"Mismatches: (\d+) in (\d+) samples", output)
        if match:
            errors = int(match.group(1))
            total = int(match.group(2))
            if total > 0:
                accuracy = 1.0 - (errors / total)
            else:
                accuracy = 0.0 
        else:
            if "FAIL" in output:
                 accuracy = 0.0
            elif "PASS" in output or "Simulation finished" in output:
                if "Mismatches:" not in output:
                     logger.warning("Could not parse mismatch count, assuming 0.0 if not explicit PASS")
                     accuracy = 0.0
            else:
                 accuracy = 0.0

        # Calculate line count
        line_count = len(code.strip().splitlines())
        
        combined_score = accuracy
        if accuracy == 1.0:
            conciseness_bonus = max(0, (100 - line_count) / 1000.0)
            combined_score += conciseness_bonus
        
        if os.path.exists(candidate_path):
            os.remove(candidate_path)
            
        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": combined_score,
        }
        
    except Exception as e:
        logger.error(f"Evaluation exception: {str(e)}")
        return {"combined_score": 0.0, "accuracy": 0.0, "error": str(e)}
        
    finally:
        if os.path.exists(executable_path):
            os.remove(executable_path)
"""

def generate_config(description, module_def):
    return f"""# Configuration for Verilog optimization
max_iterations: 50
checkpoint_interval: 10
log_level: "INFO"
language: "verilog"
file_suffix: ".v"

# LLM configuration
llm:
  models:
    - name: "gemma-local"
      model_path: "{TEMPLATE_MODEL_PATH}"
      n_ctx: 8192
      n_gpu_layers: -1
      temperature: 0.7
      top_p: 0.95
      max_tokens: 4096
      
  # Use the same model for evaluation
  evaluator_models:
    - name: "gemma-local" 
      model_path: "{TEMPLATE_MODEL_PATH}"
      n_ctx: 8192
      n_gpu_layers: -1
      temperature: 0.7
      top_p: 0.95
      max_tokens: 4096

# Prompt configuration
prompt:
  system_message: |
    You are an expert Hardware Design Engineer. Your task is to implement a Verilog module based on the following description.

    Description:
    {description}

    Interface:
    {module_def}

    Requirements:
    - Implement the module logic using `assign` statements where possible.
    - Follow Verilog-2001 standards.
    - Output ONLY the Verilog module code.
    - Do NOT include the testbench.

  # Reduce context usage
  num_top_programs: 0
  num_diverse_programs: 0
  include_artifacts: false

# Database configuration
database:
  population_size: 10 
  archive_size: 5
  num_islands: 1
  programs_per_island: 10
  elite_selection_ratio: 0.2
  exploitation_ratio: 0.7
  
  # Embedding model (CPU offloaded)
  embedding_model: "embedding_models/Nomic-Embed-Code/nomic-embed-code-q5_k_m.gguf"
  similarity_threshold: 0.95

# Evaluator configuration
evaluator:
  timeout: 30
  parallel_evaluations: 2

# Evolution settings
diff_based_evolution: false 
max_code_length: 5000
"""

def main():
    if not os.path.exists(SOURCE_DIR):
        print(f"Error: Source directory {SOURCE_DIR} not found.")
        return

    # Find all prompts to identify problems
    prompt_files = glob.glob(os.path.join(SOURCE_DIR, '*_prompt.txt'))
    
    print(f"Found {len(prompt_files)} problems to convert.")
    
    for prompt_file in prompt_files:
        filename = os.path.basename(prompt_file)
        base_name = filename.replace('_prompt.txt', '')
        
        # Identify related files
        test_file = os.path.join(SOURCE_DIR, base_name + '_test.sv')
        ifc_file = os.path.join(SOURCE_DIR, base_name + '_ifc.txt')
        ref_file = os.path.join(SOURCE_DIR, base_name + '_ref.sv') # Added ref file
        
        if not os.path.exists(test_file) or not os.path.exists(ifc_file) or not os.path.exists(ref_file):
            print(f"Skipping {base_name}: missing test, ifc or ref file.")
            continue
            
        # Create destination directory
        problem_dir = os.path.join(DEST_DIR, base_name)
        os.makedirs(problem_dir, exist_ok=True)
        
        # 1. Copy Files
        shutil.copy(test_file, os.path.join(problem_dir, 'testbench.sv'))
        shutil.copy(ref_file, os.path.join(problem_dir, 'ref.sv'))
        
        # 2. Read Interface (module definition)
        with open(ifc_file, 'r') as f:
            module_def = f.read().strip()
            
        # 3. Create initial_program.v
        with open(os.path.join(problem_dir, 'initial_program.v'), 'w') as f:
            f.write(module_def + "\n\nendmodule\n")
            
        # 4. Read Description from Prompt
        with open(prompt_file, 'r') as f:
            prompt_content = f.read()
            
        if "module" in prompt_content:
            description = prompt_content.split("module")[0].strip()
        else:
            description = prompt_content.strip()
            
        # Indent description for YAML
        description_indented = "\n    ".join(description.splitlines())
        module_def_indented = "\n    ".join(module_def.splitlines())
        
        # 5. Generate generic config
        config_content = generate_config(description_indented, module_def_indented)
        with open(os.path.join(problem_dir, 'gemma_config.yaml'), 'w') as f:
            f.write(config_content)
            
        # 6. Write Evaluator
        with open(os.path.join(problem_dir, 'evaluator.py'), 'w') as f:
            f.write(EVALUATOR_TEMPLATE)
            
        print(f"Converted {base_name}")

if __name__ == "__main__":
    main()
