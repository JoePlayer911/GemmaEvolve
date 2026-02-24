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
    Evaluates a Verilog module by running it against a reference model using Iverilog.

    Args:
        code (str): The Verilog code of the module to be evaluated.

    Returns:
        dict: A dictionary containing the evaluation results, including accuracy,
              line count, combined score, and any error messages.
    """
    try:
        # Write the candidate module to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run Iverilog to compile the design
        iverilog_cmd = ["iverilog", "-g2012", "-o", "simulation", "candidate.sv", "testbench.sv", "ref.sv"]
        iverilog_result = subprocess.run(iverilog_cmd, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run the simulation
        simulation_cmd = ["vvp", "simulation"]
        simulation_result = subprocess.run(simulation_cmd, capture_output=True, text=True)

        # Parse the simulation output
        output = simulation_result.stdout
        line_count = len(code.splitlines())
        accuracy = 1.0
        error_message = None

        if "FAIL" in output:
            accuracy = 0.0
            mismatches = re.search(r"Mismatches:\s*(\d+)\s*in\s*(\d+)", output)
            if mismatches:
                mismatches_count = int(mismatches.group(1))
                total_count = int(mismatches.group(2))
                accuracy = 1.0 - (float(mismatches_count) / float(total_count))

        elif "PASS" in output:
            accuracy = 1.0
        else:
            # Check for errors based on the specific error reporting format
            errors = re.findall(r"stats1\.errors\s*=\s*\d+", output)
            if errors:
                accuracy = 0.0
                error_message = "Errors detected in simulation output."
            
        combined_score = accuracy  # In this simplified example, the combined score is the accuracy

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": combined_score, "error": error_message}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "simulation"], check=False)
        except:
            pass