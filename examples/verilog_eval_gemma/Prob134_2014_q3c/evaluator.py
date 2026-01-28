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
    Evaluates a Verilog module by simulating it against a reference model using Iverilog and VVP.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results:
        - accuracy: The accuracy score (float).
        - line_count: The number of lines in the Verilog code.
        - combined_score: A combined score (float).
        - error: An error message (string), or None if no error occurred.
    """
    try:
        exec_name = "eval_temp"
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run Iverilog
        iverilog_cmd = f"iverilog -g2012 -o {exec_name} candidate.sv testbench.sv ref.sv"
        iverilog_result = subprocess.run(iverilog_cmd, shell=True, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run VVP
        vvp_cmd = f"{exec_name} -v"
        vvp_result = subprocess.run(vvp_cmd, shell=True, capture_output=True, text=True)

        # Parse the output
        output = vvp_result.stdout
        
        accuracy = 1.0
        mismatches = 0

        if "FAIL" in output:
            accuracy = 0.0
        elif "PASS" in output:
            accuracy = 1.0
        else:
            # Attempt to parse mismatch counts
            match = re.search(r"Mismatches:\s*(\d+)\s*in\s*Y", output)
            if match:
                mismatches = int(match.group(1))
                accuracy = 1.0 - (mismatches / 100.0)  # Assuming 100 possible mismatches

            match = re.search(r"errors\s*:\s*(\d+)", output)
            if match:
                errors = int(match.group(1))
                accuracy = max(0.0, 1.0 - (errors / 100.0)) # Ensure accuracy is not negative

        line_count = len(code.splitlines())
        combined_score = accuracy * line_count

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": combined_score, "error": None}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run(f"rm {exec_name}", shell=True)
            subprocess.run(f"rm candidate.sv", shell=True)
        except:
            pass # Ignore errors during cleanup