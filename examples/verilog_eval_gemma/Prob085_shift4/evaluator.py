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
            - line_count: The number of lines in the Verilog code (int).
            - combined_score: A combined score based on accuracy and line count (float).
            - error: An error message if any occurred (str), otherwise None.
    """
    try:
        # Write the candidate code to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "test_exec", "candidate.sv", "testbench.sv", "ref.sv"],
            capture_output=True,
            text=True
        )

        if compile_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": 0,
                "combined_score": 0.0,
                "error": compile_result.stderr
            }

        # Run the simulation
        simulation_result = subprocess.run(
            ["vvp", "test_exec"],
            capture_output=True,
            text=True
        )

        # Parse the simulation output
        output = simulation_result.stdout
        line_count = len(code.splitlines())

        accuracy = 1.0
        errors = 0
        mismatches = 0
        
        if "FAIL" in output:
            accuracy = 0.0
        else:
            # Parse mismatch counts
            match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if match:
                errors = int(match.group(1))
                mismatches = int(match.group(2))
            
            if errors > 0:
                accuracy = 1.0 - (float(errors) / mismatches)
            
            if "TIMEOUT" in output:
                accuracy = 0.5  # Penalize for timeout

        # Calculate combined score
        combined_score = accuracy * (1.0 / (line_count / 100.0))  # Normalize line count

        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": combined_score,
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
            subprocess.run(["rm", "test_exec"], check=False)
        except:
            pass