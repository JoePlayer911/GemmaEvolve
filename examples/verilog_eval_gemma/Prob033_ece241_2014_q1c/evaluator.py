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
    Evaluates a Verilog module using iverilog and vvp.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        # Create a temporary Verilog file for the candidate module
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run iverilog to compile the design
        iverilog_cmd = ["iverilog", "-g2012", "-o", "test", "candidate.sv", "testbench.sv", "ref.sv"]
        iverilog_result = subprocess.run(iverilog_cmd, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run vvp to simulate the design
        vvp_cmd = ["vvp", "test"]
        vvp_result = subprocess.run(vvp_cmd, capture_output=True, text=True)

        # Parse the simulation output
        output = vvp_result.stdout
        line_count = len(output.splitlines())

        accuracy = 1.0
        error_message = None

        if "FAIL" in output:
            accuracy = 0.0
            
        # Check for mismatch counts
        mismatch_pattern = r"Mismatches:\s*X in\s*(\w+)"
        mismatches = re.findall(mismatch_pattern, output)

        if not mismatches and "FAIL" in output:
            accuracy = 0.0
        
        if "TIMEOUT" in output:
            accuracy = 0.0
            error_message = "Simulation timed out."

        if "errors" in output and "errors_s" in output and "errors_overflow" in output:
            # Parse the error counts
            errors_match = re.search(r"stats1\.errors\s*=\s*(\d+)", output)
            errors_s_match = re.search(r"stats1\.errors_s\s*=\s*(\d+)", output)
            errors_overflow_match = re.search(r"stats1\.errors_overflow\s*=\s*(\d+)", output)

            if errors_match and errors_s_match and errors_overflow_match:
                total_errors = int(errors_match.group(1)) + int(errors_s_match.group(1)) + int(errors_overflow_match.group(1))
                if total_errors > 0:
                    accuracy = 1.0 - (total_errors / 1000) # Example: Penalize based on error count

        if "PASS" in output:
            accuracy = 1.0
        
        combined_score = accuracy

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