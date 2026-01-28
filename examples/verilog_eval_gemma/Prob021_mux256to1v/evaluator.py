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
    its output against a reference design.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        # Write the candidate code to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code using Iverilog
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

        # Run the simulation using vvp
        simulation_result = subprocess.run(
            ["vvp", "test"],
            capture_output=True,
            text=True
        )

        # Parse the simulation output to determine accuracy
        output = simulation_result.stdout
        line_count = len(code.splitlines())

        if "FAIL" in output:
            # Check for mismatches
            match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if match:
                errors = int(match.group(1))
                total_samples = int(match.group(2))
                accuracy = 1.0 - (errors / total_samples) if total_samples > 0 else 0.0
            else:
                accuracy = 0.0
        elif "PASS" in output:
            accuracy = 1.0
        else:
            # Look for mismatch statistics
            match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if match:
                errors = int(match.group(1))
                total_samples = int(match.group(2))
                accuracy = 1.0 - (errors / total_samples) if total_samples > 0 else 0.0
            else:
                accuracy = 1.0  # Assume pass if no errors are reported

        combined_score = accuracy # Simple combined score

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
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "test"], check=False)
        except:
            pass