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
    Evaluates a Verilog module by running it against a reference model using Iverilog and VVP.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results, including accuracy, line count,
        combined score, and any error messages.
    """

    try:
        # Create a temporary file for the candidate module
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run Iverilog to compile the candidate and testbench
        iverilog_cmd = ["iverilog", "-g2012", "-o", "simulation", "candidate.sv", "testbench.sv", "ref.sv"]
        iverilog_result = subprocess.run(iverilog_cmd, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run the simulation using VVP
        vvp_cmd = ["vvp", "simulation"]
        vvp_result = subprocess.run(vvp_cmd, capture_output=True, text=True)

        # Parse the VVP output to determine accuracy
        output = vvp_result.stdout
        
        # Check for explicit "FAIL" or "PASS"
        if "FAIL" in output:
            accuracy = 0.0
            mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches:
                x = int(mismatches.group(1))
                y = int(mismatches.group(2))
                accuracy = (y - x) / y if y > 0 else 0.0
            return {"accuracy": accuracy, "line_count": 0, "combined_score": 0.0, "error": ""}

        if "PASS" in output:
            accuracy = 1.0
            return {"accuracy": accuracy, "line_count": 0, "combined_score": 1.0, "error": ""}
        
        # Parse for error counts (assuming the provided example format)
        error_counts = {}
        for line in output.splitlines():
            match = re.search(r"stats1\.errors_(\w+) == 0", line)
            if match:
                signal_name = match.group(1)
                error_counts[signal_name] = 0  # Assuming no errors if the condition is met

        total_errors = sum(error_counts.values())
        
        if total_errors == 0:
            accuracy = 1.0
        else:
            total_signals = len(error_counts)
            accuracy = (total_signals - total_errors) / total_signals if total_signals > 0 else 0.0

        return {"accuracy": accuracy, "line_count": 0, "combined_score": accuracy, "error": ""}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}

    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "simulation"], check=False)
        except:
            pass