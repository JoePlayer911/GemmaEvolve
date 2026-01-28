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
    Evaluates a Verilog module by running it through Iverilog and comparing
    the output with the testbench simulation.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary with the following keys:
            accuracy: The accuracy of the module (float).
            line_count: The number of lines in the code (int).
            combined_score: A combined score based on accuracy and line count (float).
            error: An error message if any occurred (str), otherwise None.
    """
    try:
        # Create a temporary file for the Verilog code
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "test", "candidate.sv", "testbench.sv", "ref.sv"],
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
            ["vvp", "test"],
            capture_output=True,
            text=True
        )

        # Parse the simulation output
        output = simulation_result.stdout
        
        # Check for "FAIL"
        if "FAIL" in output:
            mismatches_match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches_match:
                errors = int(mismatches_match.group(1))
                total_samples = int(mismatches_match.group(2))
                accuracy = 1.0 - (errors / total_samples) if total_samples > 0 else 0.0
            else:
                accuracy = 0.0
        # Check for "PASS"
        elif "PASS" in output:
            accuracy = 1.0
        # Parse mismatches if no explicit PASS/FAIL
        else:
            mismatches_match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches_match:
                errors = int(mismatches_match.group(1))
                total_samples = int(mismatches_match.group(2))
                accuracy = 1.0 - (errors / total_samples) if total_samples > 0 else 0.0
            else:
                accuracy = 1.0  # Assume pass if no mismatches found

        # Calculate combined score
        line_count = len(code.splitlines())
        combined_score = accuracy * (1 / line_count) if line_count > 0 else 1.0

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
            subprocess.run(["rm", "test"], check=False)
        except:
            pass