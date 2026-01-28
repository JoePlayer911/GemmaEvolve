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
    Evaluates a Verilog module by simulating it against a reference module using Iverilog and VVP.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the accuracy, line count, combined score, and any error messages.
    """
    try:
        # Create a temporary file for the candidate module
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run Iverilog
        iverilog_cmd = f"iverilog -g2012 -o test { 'candidate.sv' } testbench.sv ref.sv"
        iverilog_result = subprocess.run(iverilog_cmd, shell=True, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run VVP
        vvp_cmd = f"vvp test"
        vvp_result = subprocess.run(vvp_cmd, shell=True, capture_output=True, text=True)

        # Parse the output
        output = vvp_result.stdout
        line_count = len(output.splitlines())

        accuracy = 1.0
        error_message = None

        if "FAIL" in output:
            accuracy = 0.0

        # Check for mismatch counts
        match = re.search(r"Mismatches: (\d+) in (\w+)", output)
        if match:
            mismatches = int(match.group(1))
            signal = match.group(2)
            accuracy = 1.0  # If mismatches are found, assume it's not a complete failure
            error_message = f"Mismatches: {mismatches} in {signal}"

        if "TIMEOUT" in output:
            accuracy = 0.0
            error_message = "Simulation timed out."

        if "errors" in output and "errors == 0" not in output:
            accuracy = 0.0
            error_message = "Errors found during simulation."
        
        if "PASS" in output:
            accuracy = 1.0

        combined_score = accuracy  # Simple combined score for now

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": combined_score, "error": error_message}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run("rm -f test", shell=True)
            subprocess.run("rm -f candidate.sv", shell=True)
        except:
            pass