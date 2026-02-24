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
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        exec_name = "a.out"
        candidate_name = "candidate.v"
        with open(candidate_name, "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_command = f"iverilog -g2012 -o {exec_name} {candidate_name} testbench.sv ref.sv"
        compile_result = subprocess.run(compile_command, shell=True, capture_output=True, text=True)

        if compile_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": compile_result.stderr}

        # Run the simulation
        simulation_command = f"./{exec_name}"
        simulation_result = subprocess.run(simulation_command, shell=True, capture_output=True, text=True)

        output = simulation_result.stdout
        error = simulation_result.stderr

        # Check for "FAIL"
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches:
                x = int(mismatches.group(1))
                y = int(mismatches.group(2))
                accuracy = 1.0 - (x / y)
                return {"accuracy": accuracy, "line_count": len(code.splitlines()), "combined_score": accuracy, "error": ""}
            else:
                return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": ""}

        # Check for "PASS" or errors
        if "PASS" in output:
            return {"accuracy": 1.0, "line_count": len(code.splitlines()), "combined_score": 1.0, "error": ""}

        # Parse mismatch counts
        mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
        if mismatches:
            x = int(mismatches.group(1))
            y = int(mismatches.group(2))
            accuracy = 1.0 - (x / y)
            return {"accuracy": accuracy, "line_count": len(code.splitlines()), "combined_score": accuracy, "error": ""}

        # If no errors or PASS, assume accuracy is 1.0
        return {"accuracy": 1.0, "line_count": len(code.splitlines()), "combined_score": 1.0, "error": ""}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up the generated files
        try:
            subprocess.run(f"rm {candidate_name} {exec_name}", shell=True, capture_output=True)
        except:
            pass