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
    Evaluates a Verilog module by simulating it against a reference module.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results:
        - accuracy: The accuracy of the module (float).
        - line_count: The number of lines in the module (int).
        - combined_score: A combined score based on accuracy and line count (float).
        - error: An error message if any occurred during evaluation (str).
    """

    try:
        # Write the candidate code to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "simulation", "candidate.sv", "testbench.sv", "ref.sv"],
            capture_output=True,
            text=True
        )

        if compile_result.returncode != 0:
            error_message = f"Compilation failed:\n{compile_result.stderr}"
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": error_message}

        # Run the simulation
        simulation_result = subprocess.run(
            ["vvp", "simulation"],
            capture_output=True,
            text=True
        )

        # Parse the simulation output
        output = simulation_result.stdout
        line_count = len(code.splitlines())

        accuracy = 1.0
        error_message = None

        if "FAIL" in output:
            accuracy = 0.0
        else:
            # Try to parse mismatches
            mismatches_match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches_match:
                errors = int(mismatches_match.group(1))
                clocks = int(mismatches_match.group(2))
                if errors > 0:
                    accuracy = 1.0 - (errors / clocks) if clocks > 0 else 0.0
            elif "TIMEOUT" in output:
                accuracy = 0.5  # Partial credit for timeout

            elif "PASS" in output:
                accuracy = 1.0

        # Calculate the combined score
        combined_score = accuracy * (1.0 / (line_count / 100.0))  # Normalize by line count

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": combined_score, "error": error_message}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False, capture_output=True)
            subprocess.run(["rm", "simulation"], check=False, capture_output=True)
            subprocess.run(["rm", "testbench.sv"], check=False, capture_output=True)
            subprocess.run(["rm", "ref.sv"], check=False, capture_output=True)
        except:
            pass