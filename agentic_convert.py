
import os
import shutil
import glob
import re
from llama_cpp import Llama

# Configuration
SOURCE_DIR = 'verilog-eval/dataset_code-complete-iccad2023'
DEST_DIR = 'examples/verilog_eval_gemma'
MODEL_PATH = "/home/jonathan13/GemmaEvolve/gemma-3-12b-it-Q8_0.gguf"
CONFIG_TEMPLATE_MODEL_PATH = MODEL_PATH 

# Limit for testing
LIMIT = 3

def load_model():
    print(f"Loading Gemma model from {MODEL_PATH}...")
    llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=8192,
        n_gpu_layers=-1, # GPU offload
        verbose=False
    )
    print("Model loaded.")
    return llm

def generate(llm, system_prompt, user_prompt):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    response = llm.create_chat_completion(
        messages=messages,
        temperature=0.7,
        max_tokens=4096
    )
    return response["choices"][0]["message"]["content"]

def generate_config_description(llm, prompt_content):
    system = "You are an assistant that summarizes Verilog problems."
    prompt = f"""Extract the problem description from the following text. 
    Do NOT include the module declaration/interface in the description. 
    Just describe the circuit logic and behavior concisely.

    Text:
    {prompt_content}
    """
    return generate(llm, system, prompt).strip()

def generate_initial_code(llm, interface):
    system = "You are an expert Verilog engineer."
    prompt = f"""Write a valid, compilable Verilog module skeleton based on this interface.
    Do NOT implement the logic (keep it empty or minimal).
    Ensure the module name and ports match exactly.
    
    Interface:
    {interface}
    """
    code = generate(llm, system, prompt)
    # Extract code block if present
    if "```verilog" in code:
        code = code.split("```verilog")[1].split("```")[0].strip()
    elif "```" in code:
         code = code.split("```")[1].split("```")[0].strip()
    return code

def generate_evaluator(llm, testbench_snippet):
    system = "You are a Python expert writing a test script."
    
    one_shot_example = """
import os
import subprocess
import re
import tempfile

def evaluate(code: str) -> dict:
    # Write code to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.v', prefix='verilog_', delete=False) as f:
        f.write(code)
        candidate_path = f.name
    
    executable_path = candidate_path + ".out"
    testbench_path = "testbench.sv"
    ref_path = "ref.sv" # specific to this problem

    try:
        # Compile
        compile_cmd = ["iverilog", "-g2012", "-o", executable_path, candidate_path, testbench_path, ref_path]
        subprocess.check_output(compile_cmd, stderr=subprocess.STDOUT, timeout=10)
        
        # Run
        run_cmd = ["vvp", executable_path]
        output = subprocess.check_output(run_cmd, stderr=subprocess.STDOUT, timeout=10).decode()
        
        # Parse Output (Example Logic)
        accuracy = 0.0
        if "PASS" in output:
             accuracy = 1.0
        elif "Mismatches:" in output:
             # Parse specific counts if available
             match = re.search(r"Mismatches: (\d+) in (\d+)", output)
             if match:
                 errors = int(match.group(1))
                 total = int(match.group(2))
                 accuracy = 1.0 - (errors / total)
        
        # Calculate Score
        line_count = len(code.strip().splitlines())
        combined_score = accuracy
        # bonus for conciseness only if correct
        if accuracy == 1.0:
            combined_score += max(0, (100 - line_count) / 1000.0)
            
        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": combined_score,
            "error": None
        }
    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        if os.path.exists(candidate_path):
            os.remove(candidate_path)
        if os.path.exists(executable_path):
             os.remove(executable_path)
    """

    prompt = f"""Write a Python script named `evaluator.py` that evaluates a Verilog module.
    
    GUIDELINES:
    1. Use `tempfile` for the candidate code to avoid race conditions.
    2. The `combined_score` MUST be `accuracy` plus a small bonus for `line_count`. 
       NEVER add `line_count` directly to accuracy (that would make longer code better!).
    3. The function signature MUST be: `def evaluate(code: str) -> dict:`
    
    Here is an EXAMPLE of the structure I want (do not copy it exactly, adapt it to the parsed output below):
    ```python
    {one_shot_example}
    ```

    ADAPTATION INSTRUCTIONS:
    - The testbench output you need to parse looks like this:
    ```
    {testbench_snippet}
    ```
    - Write the regex and logic to parse THIS specific output format.
    - If the output contains "Mismatches: X in Y", use that for accuracy.
    - If it only says "PASS" or "FAIL", use 1.0/0.0.
    
    Output ONLY the python code.
    """
    code = generate(llm, system, prompt)
    if "```python" in code:
        code = code.split("```python")[1].split("```")[0].strip()
    elif "```" in code:
         code = code.split("```")[1].split("```")[0].strip()
    return code


def main():
    if not os.path.exists(SOURCE_DIR):
        print(f"Error: Source directory {SOURCE_DIR} not found.")
        return

    llm = load_model()
    
    prompt_files = glob.glob(os.path.join(SOURCE_DIR, '*_prompt.txt'))
    prompt_files.sort() # Consistent order
    
    print(f"Found {len(prompt_files)} problems. Processing first {LIMIT}...")
    
    count = 0
    for prompt_file in prompt_files:
        if count >= LIMIT:
            break
            
        filename = os.path.basename(prompt_file)
        base_name = filename.replace('_prompt.txt', '')
        
        test_file = os.path.join(SOURCE_DIR, base_name + '_test.sv')
        ifc_file = os.path.join(SOURCE_DIR, base_name + '_ifc.txt')
        ref_file = os.path.join(SOURCE_DIR, base_name + '_ref.sv')
        
        if not os.path.exists(test_file) or not os.path.exists(ifc_file) or not os.path.exists(ref_file):
            print(f"Skipping {base_name}: missing test, ifc or ref file.")
            continue
            
        print(f"Converting {base_name}...")
        
        # Create output dir
        problem_dir = os.path.join(DEST_DIR, base_name)
        os.makedirs(problem_dir, exist_ok=True)
        
        # Copy static files
        shutil.copy(test_file, os.path.join(problem_dir, 'testbench.sv'))
        shutil.copy(ref_file, os.path.join(problem_dir, 'ref.sv'))
        
        # Read content
        with open(prompt_file, 'r') as f:
            prompt_content = f.read()
        with open(ifc_file, 'r') as f:
            module_def = f.read().strip()
        with open(test_file, 'r') as f:
            # Take last 20 lines of testbench to catch final reporting logic
            lines = f.readlines()
            testbench_end = "".join(lines[-30:]) 

        # 1. Generate Description
        description = generate_config_description(llm, prompt_content)
        
        # 2. Generate Initial Program
        initial_program = generate_initial_code(llm, module_def)
        with open(os.path.join(problem_dir, 'initial_program.v'), 'w') as f:
            f.write(initial_program)

        # 3. Generate Evaluator
        evaluator_code = generate_evaluator(llm, testbench_end)
        with open(os.path.join(problem_dir, 'evaluator.py'), 'w') as f:
             # Basic imports might be missing if LLM is concise, enforce them if needed
             if "import os" not in evaluator_code:
                 evaluator_code = "import os\nimport subprocess\nimport re\nimport tempfile\nimport logging\n\nlogger = logging.getLogger(__name__)\n\n" + evaluator_code
             f.write(evaluator_code)

        # 4. Generate Config
        description_indented = "\n    ".join(description.splitlines())
        config_content = f"""# Configuration for Verilog optimization
max_iterations: 50
checkpoint_interval: 10
log_level: "INFO"
language: "verilog"
file_suffix: ".v"

# LLM configuration
llm:
  models:
    - name: "gemma-local"
      model_path: "{CONFIG_TEMPLATE_MODEL_PATH}"
      n_ctx: 8192
      n_gpu_layers: -1
      temperature: 0.7
      top_p: 0.95
      max_tokens: 4096
      
  evaluator_models:
    - name: "gemma-local" 
      model_path: "{CONFIG_TEMPLATE_MODEL_PATH}"
      n_ctx: 8192
      n_gpu_layers: -1
      temperature: 0.7
      top_p: 0.95
      max_tokens: 4096

# Prompt configuration
prompt:
  system_message: |
    You are an expert Hardware Design Engineer. Your task is to implement a Verilog module.

    Description:
    {description_indented}

    Interface:
    {module_def}

    Requirements:
    - Implement the module logic using `assign` statements where possible.
    - Follow Verilog-2001 standards.
    - Output ONLY the Verilog module code.

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
        with open(os.path.join(problem_dir, 'gemma_config.yaml'), 'w') as f:
            f.write(config_content)

        count += 1
        print(f"Finished {base_name}")

if __name__ == "__main__":
    main()
