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
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        # Create a temporary file for the candidate module
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "simulation", "candidate.sv", "testbench.sv", "ref.sv"],
            capture_output=True,
            text=True
        )

        if compile_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": compile_result.stderr}

        # Run the simulation
        simulation_result = subprocess.run(
            ["vvp", "simulation"],
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
        else:
            # Check for mismatch counts
            mismatch_pattern = re.compile(r"Mismatches:\s*X in\s*(\w+)")
            mismatches = mismatch_pattern.findall(output)
            if mismatches:
                accuracy = 0.5  # Penalize for mismatches

            if "errors" in output and "errors_q" in output and "errors_state" in output:
                errors = int(re.search(r"stats1\.errors = (\d+);", output).group(1))
                if errors > 0:
                    accuracy = 0.5

            if "TIMEOUT" in output:
                accuracy = 0.0

        combined_score = accuracy

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": combined_score, "error": error_message}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "simulation"], check=False)
        except:
            pass