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
        code (str): The Verilog code of the module to be evaluated.

    Returns:
        dict: A dictionary containing the evaluation results:
            - accuracy (float): The accuracy of the module (1.0 for pass, 0.0 for fail).
            - line_count (int): The number of lines in the Verilog code.
            - combined_score (float): A combined score based on accuracy and line count.
            - error (str): An error message if any occurred during the evaluation, otherwise None.
    """

    try:
        # Create a temporary file for the candidate module
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "simulation", "candidate.sv", "testbench.sv", "ref.sv"],
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
        simulation_result = subprocess.run(
            ["vvp", "simulation"],
            capture_output=True,
            text=True
        )

        # Parse the simulation output
        output = simulation_result.stdout
        line_count = len(code.splitlines())

        if "FAIL" in output:
            accuracy = 0.0
            mismatches_match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches_match:
                errors = int(mismatches_match.group(1))
                clocks = int(mismatches_match.group(2))
                accuracy = 1.0 - (errors / clocks) if clocks > 0 else 0.0
            return {
                "accuracy": accuracy,
                "line_count": line_count,
                "combined_score": accuracy * (1.0 / line_count),
                "error": None
            }

        if "PASS" in output:
            accuracy = 1.0
        else:
            mismatches_match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches_match:
                errors = int(mismatches_match.group(1))
                clocks = int(mismatches_match.group(2))
                accuracy = 1.0 - (errors / clocks) if clocks > 0 else 1.0
            else:
                accuracy = 1.0

        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": accuracy * (1.0 / line_count),
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
            subprocess.run(["rm", "simulation"], check=False)
        except:
            pass