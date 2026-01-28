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
    Evaluates a Verilog module by simulating it against a reference module using Iverilog and Verilator.

    Args:
        code (str): The Verilog code of the module to be evaluated.

    Returns:
        dict: A dictionary containing the evaluation results, including accuracy, line count,
              combined score, and any error messages.
    """

    try:
        # Create a temporary file for the candidate module
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "test_exec", "candidate.sv", "testbench.sv", "ref.sv"],
            capture_output=True,
            text=True
        )
        if compile_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": compile_result.stderr}

        # Run the simulation
        simulation_result = subprocess.run(
            ["vvp", "test_exec"],
            capture_output=True,
            text=True
        )

        # Parse the simulation output
        output = simulation_result.stdout
        line_count = len(output.splitlines())

        # Check for "FAIL"
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches:\s*(\w+) in (\w+)", output)
            if mismatches:
                return {"accuracy": 0.0, "line_count": line_count, "combined_score": 0.0, "error": "FAIL with mismatches"}
            else:
                return {"accuracy": 0.0, "line_count": line_count, "combined_score": 0.0, "error": "FAIL"}

        # Check for "PASS"
        if "PASS" in output:
            return {"accuracy": 1.0, "line_count": line_count, "combined_score": 1.0, "error": None}

        # Check for errors based on mismatch counts
        ringer_errors = re.search(r"stats1\.errors_ringer = (\d+)", output)
        motor_errors = re.search(r"stats1\.errors_motor = (\d+)", output)
        total_errors = re.search(r"stats1\.errors = (\d+)", output)

        if total_errors:
            total_errors = int(total_errors.group(1))
            if total_errors > 0:
                return {"accuracy": 0.0, "line_count": line_count, "combined_score": 0.0, "error": f"Errors found: {total_errors}"}
            else:
                return {"accuracy": 1.0, "line_count": line_count, "combined_score": 1.0, "error": None}

        # If no explicit PASS or FAIL is found, assume PASS
        return {"accuracy": 1.0, "line_count": line_count, "combined_score": 1.0, "error": None}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "test_exec"], check=False)
            subprocess.run(["rm", "candidate.sv"], check=False)
        except:
            pass