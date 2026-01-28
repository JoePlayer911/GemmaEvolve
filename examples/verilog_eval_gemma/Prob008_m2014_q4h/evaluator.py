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
    Evaluates a Verilog module by running it through a simulation and analyzing the output.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results, including accuracy, line count,
        combined score, and any error messages.
    """
    try:
        # Write the candidate code to a temporary file
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
                "error": f"Iverilog compilation failed: {compile_result.stderr}"
            }

        # Run the simulation using VVP
        simulation_result = subprocess.run(
            ["vvp", "simulation"],
            capture_output=True,
            text=True
        )

        output = simulation_result.stdout
        
        # Check for "FAIL" in the output
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches:
                errors = int(mismatches.group(1))
                clocks = int(mismatches.group(2))
                accuracy = 1.0 - (float(errors) / clocks) if clocks > 0 else 0.0
            else:
                accuracy = 0.0
        # Check for "PASS" in the output
        elif "PASS" in output:
            accuracy = 1.0
        else:
            # Parse mismatch counts from the output
            mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches:
                errors = int(mismatches.group(1))
                clocks = int(mismatches.group(2))
                accuracy = 1.0 - (float(errors) / clocks) if clocks > 0 else 0.0
            else:
                accuracy = 1.0  # Assume pass if no mismatches found

        # Calculate line count
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
        except:
            pass