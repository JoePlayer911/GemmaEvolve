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
    its output to a reference design.

    Args:
        code: The Verilog code to evaluate.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
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
            accuracy = 0.0
            mismatch_pattern = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatch_pattern:
                mismatches = int(mismatch_pattern.group(1))
                total_samples = int(mismatch_pattern.group(2))
                accuracy = 1.0 - (mismatches / total_samples)
            return {
                "accuracy": accuracy,
                "line_count": line_count,
                "combined_score": accuracy,
                "error": ""
            }

        if "PASS" in output:
            accuracy = 1.0
        else:
            mismatch_pattern = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatch_pattern:
                mismatches = int(mismatch_pattern.group(1))
                total_samples = int(mismatch_pattern.group(2))
                accuracy = 1.0 - (mismatches / total_samples)
            else:
                accuracy = 1.0

        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": accuracy,
            "error": ""
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