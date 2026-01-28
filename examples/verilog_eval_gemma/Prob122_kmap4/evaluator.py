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
    Evaluates a Verilog module.

    Args:
        code: The Verilog code of the module to evaluate.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        # Write the candidate module to a file
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
                "error": compile_result.stderr
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
            # Check for mismatch counts
            mismatch_pattern = r"Mismatches: (\d+) in (\d+)"
            match = re.search(mismatch_pattern, output)
            if match:
                errors = int(match.group(1))
                clocks = int(match.group(2))
                accuracy = 1.0 - (float(errors) / clocks) if clocks > 0 else 0.0
            else:
                accuracy = 0.0
        elif "PASS" in output:
            accuracy = 1.0
        else:
            # Attempt to parse mismatch counts
            mismatch_pattern = r"Mismatches: (\d+) in (\d+)"
            match = re.search(mismatch_pattern, output)
            if match:
                errors = int(match.group(1))
                clocks = int(match.group(2))
                accuracy = 1.0 - (float(errors) / clocks) if clocks > 0 else 0.0
            else:
                accuracy = 1.0 # Assume pass if no errors are found

        combined_score = accuracy  # In this simple case, accuracy is the combined score

        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": combined_score,
            "error": ""
        }
    except Exception as e:
        return {
            "accuracy": 0.0,
            "line_count": len(code.splitlines()),
            "combined_score": 0.0,
            "error": str(e)
        }