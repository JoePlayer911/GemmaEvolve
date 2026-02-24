import os
import subprocess
import re
import tempfile
import logging

logger = logging.getLogger(__name__)

import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it against a reference model using Iverilog and Verilator.

    Args:
        code (str): The Verilog code of the module to be evaluated.

    Returns:
        dict: A dictionary containing the evaluation results.  Keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        # Create a temporary Verilog file for the candidate module
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run Iverilog
        iverilog_cmd = ["iverilog", "-g2012", "-o", "test", "candidate.sv", "testbench.sv", "ref.sv"]
        iverilog_result = subprocess.run(iverilog_cmd, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run Verilator
        vvp_result = subprocess.run(["vvp", "test"], capture_output=True, text=True)

        # Parse the output for mismatches and errors
        output = vvp_result.stdout
        accuracy = 1.0
        error_message = ""

        if "FAIL" in output:
            accuracy = 0.0
            
        if "PASS" in output:
            accuracy = 1.0

        # Parse for mismatch counts using regex
        mismatch_pattern = re.compile(r"Mismatches: (.*?)\s*in\s*(.*)")
        mismatches = mismatch_pattern.findall(output)

        if mismatches and accuracy == 0.0:
            accuracy = 0.0
            
        #If no errors found, accuracy is 1.0
        if "errors" not in output and "TIMEOUT" not in output and "FAIL" not in output:
            accuracy = 1.0
        
        # Count lines in the candidate code
        line_count = len(code.splitlines())
        
        # Combined score (simple: accuracy * line_count)
        combined_score = accuracy * line_count

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": combined_score, "error": error_message}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "test"], check=False)
        except:
            pass