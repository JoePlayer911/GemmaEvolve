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
        A dictionary containing the evaluation results:
        - accuracy: The accuracy score (float).
        - line_count: The number of lines in the Verilog code (int).
        - combined_score: A combined score based on accuracy and line count (float).
        - error: An error message if any occurred during the evaluation (str).
    """
    try:
        # Save the candidate module to a file
        candidate_file = "candidate.sv"
        with open(candidate_file, "w") as f:
            f.write(code)

        # Run Iverilog
        iverilog_cmd = f"iverilog -g2012 -o testbench testbench.sv {candidate_file} ref.sv"
        iverilog_result = subprocess.run(iverilog_cmd, shell=True, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": f"Iverilog error: {iverilog_result.stderr}"}

        # Run the simulation
        vvp_cmd = "./testbench"
        vvp_result = subprocess.run(vvp_cmd, shell=True, capture_output=True, text=True)

        # Parse the simulation output
        output = vvp_result.stdout
        
        # Check for "FAIL"
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches:\s*(\w+)\s*in\s*(\w+)", output)
            if mismatches:
                return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": f"FAIL with mismatches: {mismatches.groups()}"}
            else:
                return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": "FAIL without mismatches"}

        # Check for "PASS"
        if "PASS" in output:
            return {"accuracy": 1.0, "line_count": len(code.splitlines()), "combined_score": 1.0, "error": None}

        # Parse mismatch counts from the output (if present)
        mismatches_x = re.search(r"stats1\.errors\s*=\s*(\d+)", output)
        mismatches_out_bytes = re.search(r"stats1\.errors_out_bytes\s*=\s*(\d+)", output)
        mismatches_done = re.search(r"stats1\.errors_done\s*=\s*(\d+)", output)

        total_errors = 0
        if mismatches_x:
            total_errors += int(mismatches_x.group(1))
        if mismatches_out_bytes:
            total_errors += int(mismatches_out_bytes.group(1))
        if mismatches_done:
            total_errors += int(mismatches_done.group(1))
        
        if total_errors > 0:
            accuracy = 1.0 - (float(total_errors) / 1000.0) # Assuming max 1000 cycles
            accuracy = max(0.0, min(accuracy, 1.0)) # Clamp between 0 and 1
            return {"accuracy": accuracy, "line_count": len(code.splitlines()), "combined_score": accuracy, "error": f"Mismatches found: {total_errors}"}

        return {"accuracy": 1.0, "line_count": len(code.splitlines()), "combined_score": 1.0, "error": None}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}