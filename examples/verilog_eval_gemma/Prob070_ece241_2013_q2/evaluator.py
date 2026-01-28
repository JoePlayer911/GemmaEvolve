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
        A dictionary containing the accuracy, line count, combined score, and error message.
    """
    try:
        # Write the code to a temporary file
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

        # Check for explicit FAIL
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches:\s*(\w+)\s*in\s*(\w+)", output)
            if mismatches:
                return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": "FAIL with mismatches"}
            else:
                return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": "FAIL"}
        
        # Check for PASS
        if "PASS" in output:
            return {"accuracy": 1.0, "line_count": 0, "combined_score": 1.0, "error": None}

        # Parse mismatch counts if present
        mismatches = re.findall(r"Mismatches:\s*(\d+)\s*in\s*(\w+)", output)
        if mismatches:
            total_mismatches = sum(int(count) for count, _ in mismatches)
            # You can adjust the accuracy calculation based on the total mismatches
            accuracy = 1.0 - (total_mismatches / 1000.0)  # Example: Reduce accuracy by total mismatches / 1000
            accuracy = max(0.0, min(1.0, accuracy))  # Ensure accuracy is within 0.0 and 1.0
            return {"accuracy": accuracy, "line_count": 0, "combined_score": accuracy, "error": "Mismatches found"}

        # If no errors are found, assume PASS
        return {"accuracy": 1.0, "line_count": 0, "combined_score": 1.0, "error": None}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "simulation"], check=False)
        except FileNotFoundError:
            pass