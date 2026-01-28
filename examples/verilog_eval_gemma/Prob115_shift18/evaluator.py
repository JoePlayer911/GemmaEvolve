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
            - error: An error message if any occurred during evaluation (str), otherwise None.
    """
    try:
        # Create a temporary file for the candidate module
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "sim", "candidate.sv", "testbench.sv", "ref.sv"],
            capture_output=True,
            text=True
        )

        if compile_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": len(code.splitlines()),
                "combined_score": 0.0,
                "error": f"Compilation error: {compile_result.stderr}"
            }

        # Run the simulation
        sim_result = subprocess.run(
            ["vvp", "sim"],
            capture_output=True,
            text=True
        )

        output = sim_result.stdout
        
        # Check for "FAIL"
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches:
                errors = int(mismatches.group(1))
                clocks = int(mismatches.group(2))
                accuracy = 1.0 - (errors / clocks) if clocks > 0 else 0.0
            else:
                accuracy = 0.0
        # Check for "PASS"
        elif "PASS" in output:
            accuracy = 1.0
        # Parse mismatches from the output
        else:
            mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches:
                errors = int(mismatches.group(1))
                clocks = int(mismatches.group(2))
                accuracy = 1.0 - (errors / clocks) if clocks > 0 else 0.0
            else:
                accuracy = 1.0

        line_count = len(code.splitlines())
        combined_score = accuracy * (1.0 / line_count) if line_count > 0 else 0.0
        
        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": combined_score,
            "error": None
        }

    except Exception as e:
        return {
            "accuracy": 0.0,
            "line_count": len(code.splitlines()),
            "combined_score": 0.0,
            "error": str(e)
        }
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "sim"], check=False)
        except:
            pass