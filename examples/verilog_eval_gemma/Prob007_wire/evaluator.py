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
            - combined_score: A combined score (float).  Currently accuracy.
            - error: An error message (str), or None if no error occurred.
    """

    try:
        # Create a temporary file for the candidate module
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code using Iverilog
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

        # Run the simulation using VVP
        simulation_result = subprocess.run(
            ["vvp", "simulation"],
            capture_output=True,
            text=True
        )

        # Parse the simulation output to determine accuracy
        output = simulation_result.stdout
        accuracy = 1.0
        errors = 0
        mismatches = 0

        if "FAIL" in output:
            accuracy = 0.0

        # Attempt to parse mismatch counts from the output
        mismatch_pattern = re.compile(r"Mismatches: (\d+) in (\d+)")
        match = mismatch_pattern.search(output)
        if match:
            errors = int(match.group(1))
            mismatches = int(match.group(2))
        
        if "TIMEOUT" in output:
            accuracy = 0.0

        if errors == 0 and "PASS" not in output:
            accuracy = 1.0
        
        if errors > 0:
            accuracy = 1.0 - (float(errors) / mismatches) if mismatches > 0 else 0.0

        line_count = len(code.splitlines())
        combined_score = accuracy

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
            subprocess.run(["rm", "simulation"], check=False)
            subprocess.run(["rm", "testbench.sv"], check=False)
            subprocess.run(["rm", "ref.sv"], check=False)
        except:
            pass