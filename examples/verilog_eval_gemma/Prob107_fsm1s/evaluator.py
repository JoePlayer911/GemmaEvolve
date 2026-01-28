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
    Evaluates a Verilog module by running it against a testbench.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results:
            - accuracy: The accuracy score (float).
            - line_count: The number of lines in the Verilog code (int).
            - combined_score: A combined score based on accuracy and line count (float).
            - error: An error message, if any (str).
    """
    try:
        exec_name = "temp_exec"
        # Write the Verilog code to a file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", exec_name, "candidate.sv", "testbench.sv", "ref.sv"],
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
            [exec_name],
            capture_output=True,
            text=True
        )

        output = simulation_result.stdout

        # Check for explicit "FAIL"
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
                "combined_score": accuracy * (1.0 / len(code.splitlines())),
                "error": None
            }

        # Check for explicit "PASS"
        if "PASS" in output:
            accuracy = 1.0
        else:
            # Parse mismatch counts
            mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches:
                errors = int(mismatches.group(1))
                total_samples = int(mismatches.group(2))
                accuracy = 1.0 - (float(errors) / total_samples) if total_samples > 0 else 0.0
            else:
                accuracy = 1.0  # Assume pass if no mismatches found

        return {
            "accuracy": accuracy,
            "line_count": len(code.splitlines()),
            "combined_score": accuracy * (1.0 / len(code.splitlines())),
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
        # Clean up the executable
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", exec_name], check=False)
        except:
            pass