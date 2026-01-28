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
    Evaluates a Verilog module by comparing its output against a reference model.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results.
    """

    exec_name = "temp_exec"
    try:
        # Write the candidate code to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", exec_name, "candidate.sv", "testbench.sv", "ref.sv"],
            capture_output=True,
            text=True,
        )

        if compile_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": 0,
                "combined_score": 0.0,
                "error": compile_result.stderr,
            }

        # Run the simulation
        sim_result = subprocess.run(
            [exec_name], capture_output=True, text=True
        )

        # Parse the simulation output
        output = sim_result.stdout
        accuracy = 1.0
        error_message = ""

        if "FAIL" in output:
            accuracy = 0.0
        else:
            # Check for mismatches
            mismatch_pattern = re.compile(r"Mismatches:.*X in (\w+)")
            mismatches = mismatch_pattern.findall(output)
            if mismatches:
                accuracy = 0.5  # Penalize for mismatches, but not a complete failure

            # Check for errors based on the provided example
            error_pattern = re.compile(r"stats1\.errors > 0")
            if error_pattern.search(output):
                accuracy = 0.0

            if "TIMEOUT" in output:
                accuracy = 0.0

        # Count lines in the code
        line_count = len(code.splitlines())

        combined_score = accuracy  # Simple combined score for now

        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": combined_score,
            "error": error_message,
        }
    except Exception as e:
        return {
            "accuracy": 0.0,
            "line_count": 0,
            "combined_score": 0.0,
            "error": str(e),
        }
    finally:
        # Clean up the temporary executable
        try:
            subprocess.run(["rm", exec_name], check=False)
        except FileNotFoundError:
            pass
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
        except FileNotFoundError:
            pass