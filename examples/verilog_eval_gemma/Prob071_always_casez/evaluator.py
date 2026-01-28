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
    Evaluates a Verilog module by running a simulation against a reference model.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results:
        - accuracy: The accuracy score (float).
        - line_count: The number of lines in the Verilog code (int).
        - combined_score: A combined score (float).
        - error: An error message (str), or None if no errors occurred.
    """

    try:
        # Create a temporary file for the candidate module
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "test_exec", "candidate.sv", "testbench.sv", "ref.sv"],
            capture_output=True,
            text=True,
        )

        if compile_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": len(code.splitlines()),
                "combined_score": 0.0,
                "error": compile_result.stderr,
            }

        # Run the simulation
        simulation_result = subprocess.run(
            ["vvp", "test_exec"], capture_output=True, text=True
        )

        output = simulation_result.stdout
        error = simulation_result.stderr

        # Check for "FAIL"
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches:
                errors = int(mismatches.group(1))
                total_samples = int(mismatches.group(2))
                accuracy = 1.0 - (float(errors) / total_samples) if total_samples > 0 else 0.0
            else:
                accuracy = 0.0
            return {
                "accuracy": accuracy,
                "line_count": len(code.splitlines()),
                "combined_score": accuracy,
                "error": None,
            }

        # Check for "PASS" or mismatches
        if "PASS" in output:
            accuracy = 1.0
        else:
            mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches:
                errors = int(mismatches.group(1))
                total_samples = int(mismatches.group(2))
                accuracy = 1.0 - (float(errors) / total_samples) if total_samples > 0 else 0.0
            else:
                accuracy = 1.0
        
        return {
            "accuracy": accuracy,
            "line_count": len(code.splitlines()),
            "combined_score": accuracy,
            "error": None,
        }

    except Exception as e:
        return {
            "accuracy": 0.0,
            "line_count": len(code.splitlines()),
            "combined_score": 0.0,
            "error": str(e),
        }
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "test_exec"], check=False)
        except FileNotFoundError:
            pass