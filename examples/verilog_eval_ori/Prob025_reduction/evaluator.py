import os
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
