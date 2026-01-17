import os
import subprocess
import re
import tempfile
import logging

logger = logging.getLogger(__name__)

def evaluate(code: str) -> dict:
    """
    Evaluate Verilog code using Icarus Verilog.
    
    Args:
        code: The Verilog source code to evaluate
        
    Returns:
        Dictionary containing metrics (accuracy, line_count, combined_score)
    """
    # If the input is a file path, read the code from it
    if os.path.exists(code) and os.path.isfile(code):
        with open(code, 'r') as f:
            code = f.read()

    # Write code to temp file
    # We use a fixed prefix to easily identify these files if cleanup fails
    with tempfile.NamedTemporaryFile(mode='w', suffix='.v', prefix='verilog_eval_', delete=False) as f:
        f.write(code)
        candidate_path = f.name
    
    # Path to testbench (relative to project root)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    testbench_path = os.path.join(script_dir, "testbench.v")
    executable_path = candidate_path + ".out"
    
    try:
        # Log the code we are about to compile (first 5 lines)
        logger.info(f"Compiling code (first 5 lines): {code.splitlines()[:5]}")

        # 1. Compile using iverilog
        # iverilog -o <exec> <candidate> <testbench>
        compile_cmd = ["iverilog", "-o", executable_path, candidate_path, testbench_path]
        try:
            subprocess.check_output(compile_cmd, stderr=subprocess.STDOUT, timeout=10)
        except subprocess.CalledProcessError as e:
            error_msg = e.output.decode()
            logger.warning(f"Compilation failed: {error_msg}")
            # Do NOT remove candidate_path if compilation failed, for debugging
            logger.info(f"Retained failing file at: {candidate_path}")
            return {"combined_score": 0.0, "accuracy": 0.0, "error": f"Compilation failed: {candidate_path}: {error_msg}"}
        
        # 2. Run simulation using vvp
        run_cmd = ["vvp", executable_path]
        try:
            output = subprocess.check_output(run_cmd, stderr=subprocess.STDOUT, timeout=5).decode()
        except subprocess.CalledProcessError as e:
            error_msg = e.output.decode()
            logger.warning(f"Runtime error: {error_msg}")
            return {"combined_score": 0.0, "accuracy": 0.0, "error": f"Runtime error: {error_msg}"}
        
        # 3. Parse output
        accuracy = 0.0
        match = re.search(r"SUMMARY: Passed (\d+)/(\d+) tests", output)
        if match:
            passed = int(match.group(1))
            total = int(match.group(2))
            accuracy = passed / total
        else:
            logger.warning("Could not parse test summary from output")
            return {"combined_score": 0.0, "accuracy": 0.0, "error": "Could not parse output"}
            
        # Calculate line count for "conciseness" metric (secondary objective)
        line_count = len(code.strip().splitlines())
        
        # Combined score: 
        # Primary: Accuracy (0.0 - 1.0)
        # Secondary: Conciseness (bonus for shorter code if accuracy is 100%)
        
        combined_score = accuracy
        if accuracy == 1.0:
            # Add small bonus for conciseness (fewer lines is better)
            # Normalize: 100 lines -> 0 bonus, 10 lines -> 0.09 bonus
            conciseness_bonus = max(0, (100 - line_count) / 1000.0)
            combined_score += conciseness_bonus
        
        # Cleanup successful files
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
        # Cleanup executables
        if os.path.exists(executable_path):
            os.remove(executable_path)
