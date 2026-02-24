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
    Evaluates a Verilog module by simulating it against a reference module using Iverilog and VVP.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results:
        - accuracy: The accuracy score (float between 0.0 and 1.0).
        - line_count: The number of lines in the candidate Verilog code.
        - combined_score: A combined score based on accuracy and line count (not implemented yet).
        - error: An error message if any occurred during the evaluation (None if no errors).
    """

    try:
        # Write the candidate module to a file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "test_exec", "candidate.sv", "testbench.sv", "ref.sv"],
            capture_output=True,
            text=True,
        )
        if compile_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": compile_result.stderr}

        # Run the simulation
        simulation_result = subprocess.run(
            ["vvp", "test_exec"], capture_output=True, text=True
        )

        # Parse the simulation output
        output = simulation_result.stdout
        line_count = len(code.splitlines())

        if "FAIL" in output:
            accuracy = 0.0
            mismatches = re.search(r"Mismatches:\s*X in\s*(\w+)", output)
            if mismatches:
                accuracy = 0.0  # Fail due to FAIL, but note mismatches
            return {"accuracy": accuracy, "line_count": line_count, "combined_score": 0.0, "error": None}

        if "PASS" in output:
            accuracy = 1.0
            return {"accuracy": accuracy, "line_count": line_count, "combined_score": 1.0, "error": None}

        # Check for errors based on statistics in the Verilog output
        error_pattern = re.search(r"stats1\.errors\s*=\s*\d+", output)
        if error_pattern:
            errors_found = int(re.search(r"stats1\.errors\s*=\s*(\d+)", output).group(1))
            if errors_found > 0:
                accuracy = 0.0
                return {"accuracy": accuracy, "line_count": line_count, "combined_score": 0.0, "error": "Errors found during simulation."}

        accuracy = 1.0
        return {"accuracy": accuracy, "line_count": line_count, "combined_score": 1.0, "error": None}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up the generated files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "test_exec"], check=False)
        except:
            pass