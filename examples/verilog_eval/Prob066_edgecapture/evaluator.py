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
        # Write the code to a temporary file
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
        line_count = len(output.splitlines())

        accuracy = 1.0
        error_message = None

        if "FAIL" in output:
            accuracy = 0.0

        # Parse mismatch counts
        mismatch_pattern = r"Mismatches:\s*(\d+)\s*in\s*(\d+)"
        match = re.search(mismatch_pattern, output)
        if match:
            errors = int(match.group(1))
            total_samples = int(match.group(2))
            if errors > 0:
                accuracy = 1.0 - (float(errors) / total_samples)

        if "TIMEOUT" in output:
            accuracy = 0.0

        if "errors_out" in output:
            error_message = "errors_out detected"
            accuracy = 0.0

        if accuracy == 0.0 and "FAIL" not in output and "TIMEOUT" not in output:
            error_message = "Simulation failed but no explicit FAIL message."

        combined_score = accuracy  # Simple combined score for now

        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": combined_score,
            "error": error_message
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