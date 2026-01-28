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
    Evaluates a Verilog module by running it against a testbench.

    Args:
        code: The Verilog code of the module to evaluate.

    Returns:
        A dictionary containing the accuracy, line count, combined score, and error message.
    """
    try:
        # Write the candidate module to a file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run Icarus Verilog
        iverilog_cmd = ["iverilog", "-g2012", "-o", "test", "candidate.sv", "testbench.sv", "ref.sv"]
        iverilog_result = subprocess.run(iverilog_cmd, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run the simulation
        vvp_cmd = ["vvp", "test"]
        vvp_result = subprocess.run(vvp_cmd, capture_output=True, text=True)

        # Parse the output
        output = vvp_result.stdout
        line_count = len(output.splitlines())

        if "FAIL" in output:
            mismatches = re.search(r"Mismatches:\s*(\d+)\s*in\s*(\d+)", output)
            if mismatches:
                x = int(mismatches.group(1))
                y = int(mismatches.group(2))
                accuracy = 1.0 - (x / y)
                return {"accuracy": accuracy, "line_count": line_count, "combined_score": accuracy, "error": ""}
            else:
                accuracy = 0.0
                return {"accuracy": accuracy, "line_count": line_count, "combined_score": accuracy, "error": ""}

        if "PASS" in output:
            accuracy = 1.0
            return {"accuracy": accuracy, "line_count": line_count, "combined_score": accuracy, "error": ""}

        # Check for errors based on the provided example output
        error_counts = {}
        error_counts["stats1.errors"] = 0
        error_counts["stats1.errors_out_both"] = 0
        error_counts["stats1.errors_out_any"] = 0
        error_counts["stats1.errors_out_different"] = 0

        for line in output.splitlines():
            if "stats1.errors++" in line:
                error_counts["stats1.errors"] += 1
            if "stats1.errors_out_both = stats1.errors_out_both+1'b1" in line:
                error_counts["stats1.errors_out_both"] += 1
            if "stats1.errors_out_any = stats1.errors_out_any+1'b1" in line:
                error_counts["stats1.errors_out_any"] += 1
            if "stats1.errors_out_different = stats1.errors_out_different+1'b1" in line:
                error_counts["stats1.errors_out_different"] += 1

        total_errors = sum(error_counts.values())

        if total_errors > 0:
            accuracy = 1.0 - (total_errors / 1000)  # Assuming 1000 is a reasonable max error count
            return {"accuracy": accuracy, "line_count": line_count, "combined_score": accuracy, "error": ""}
        else:
            accuracy = 1.0
            return {"accuracy": accuracy, "line_count": line_count, "combined_score": accuracy, "error": ""}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}