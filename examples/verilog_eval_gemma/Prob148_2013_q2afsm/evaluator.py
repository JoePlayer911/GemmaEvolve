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
    Evaluates a Verilog module by simulating it against a reference model.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results:
            - accuracy: The accuracy score (float).
            - line_count: The number of lines in the code (int).
            - combined_score: A combined score based on accuracy and line count (float).
            - error: An error message (str), or None if no error occurred.
    """
    try:
        # Write the code to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run IVerilog
        iverilog_cmd = ["iverilog", "-g2012", "-o", "simulation", "candidate.sv", "testbench.sv", "ref.sv"]
        iverilog_result = subprocess.run(iverilog_cmd, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": 0,
                "combined_score": 0.0,
                "error": f"Iverilog compilation failed:\n{iverilog_result.stderr}"
            }

        # Run the simulation
        vvp_cmd = ["vvp", "simulation"]
        vvp_result = subprocess.run(vvp_cmd, capture_output=True, text=True)

        # Parse the simulation output
        output = vvp_result.stdout
        
        if "FAIL" in output:
            accuracy = 0.0
            
            # Attempt to parse mismatch counts
            mismatch_pattern = r"Mismatches: (\d+) in (\d+)"
            match = re.search(mismatch_pattern, output)
            if match:
                errors = int(match.group(1))
                clocks = int(match.group(2))
                accuracy = 1.0 - (errors / clocks) if clocks > 0 else 0.0

            return {
                "accuracy": accuracy,
                "line_count": len(code.splitlines()),
                "combined_score": accuracy * (100 / len(code.splitlines())),
                "error": None
            }

        # Check for PASS or mismatches
        if "PASS" in output:
            accuracy = 1.0
        else:
            # Parse mismatch counts
            mismatch_pattern = r"Mismatches: (\d+) in (\d+)"
            match = re.search(mismatch_pattern, output)
            if match:
                errors = int(match.group(1))
                clocks = int(match.group(2))
                accuracy = 1.0 - (errors / clocks) if clocks > 0 else 0.0
            else:
                accuracy = 1.0  # Assume pass if no explicit mismatch found
        

        return {
            "accuracy": accuracy,
            "line_count": len(code.splitlines()),
            "combined_score": accuracy * (100 / len(code.splitlines())),
            "error": None
        }

    except Exception as e:
        return {
            "accuracy": 0.0,
            "line_count": 0,
            "combined_score": 0.0,
            "error": str(e)
        }
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "simulation"], check=False)
            subprocess.run(["rm", "testbench.sv"], check=False)
            subprocess.run(["rm", "ref.sv"], check=False)
        except FileNotFoundError:
            pass