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
    Evaluates a Verilog module by running it through Iverilog and comparing the output
    to a reference simulation.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the accuracy, line count, combined score, and any error messages.
    """
    try:
        # Create a temporary file for the candidate module.
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run Iverilog to compile the candidate and testbench modules.
        iverilog_cmd = ["iverilog", "-g2012", "-o", "simulation", "candidate.sv", "testbench.sv", "ref.sv"]
        iverilog_result = subprocess.run(iverilog_cmd, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run the simulation.
        simulation_cmd = ["vvp", "simulation"]
        simulation_result = subprocess.run(simulation_cmd, capture_output=True, text=True)

        # Parse the simulation output to determine accuracy.
        output = simulation_result.stdout
        
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches:
                errors = int(mismatches.group(1))
                clocks = int(mismatches.group(2))
                accuracy = 1.0 - (float(errors) / clocks) if clocks > 0 else 0.0
            else:
                accuracy = 0.0
        elif "PASS" in output:
            accuracy = 1.0
        else:
            mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches:
                errors = int(mismatches.group(1))
                clocks = int(mismatches.group(2))
                accuracy = 1.0 - (float(errors) / clocks) if clocks > 0 else 0.0
            else:
                accuracy = 1.0

        return {"accuracy": accuracy, "line_count": len(code.splitlines()), "combined_score": accuracy, "error": None}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files.
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "simulation"], check=False)
        except FileNotFoundError:
            pass