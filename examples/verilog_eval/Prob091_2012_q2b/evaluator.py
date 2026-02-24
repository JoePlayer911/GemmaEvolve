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
    Evaluates a Verilog module by running Iverilog and comparing the output
    against a reference design.

    Args:
        code (str): The Verilog code of the module to be evaluated.

    Returns:
        dict: A dictionary containing the evaluation results, including accuracy,
              line count, combined score, and any error messages.
    """

    try:
        # Write the code to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run Iverilog
        iverilog_cmd = ["iverilog", "-g2012", "-o", "test", "candidate.sv", "testbench.sv", "ref.sv"]
        iverilog_result = subprocess.run(iverilog_cmd, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run the simulation
        vvp_cmd = ["vvp", "test"]
        vvp_result = subprocess.run(vvp_cmd, capture_output=True, text=True)

        # Parse the output
        output = vvp_result.stdout

        # Check for explicit "FAIL"
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches:\s*(.*)", output)
            if mismatches:
                return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": "FAIL with mismatches"}
            else:
                return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": "FAIL"}

        # Check for explicit "PASS"
        if "PASS" in output:
            return {"accuracy": 1.0, "line_count": len(code.splitlines()), "combined_score": 1.0, "error": None}

        # Check for errors based on mismatch counts
        mismatches = re.search(r"errors_Y1\s*=\s*(\d+)", output)
        errors_Y1 = int(mismatches.group(1)) if mismatches else 0
        mismatches = re.search(r"errors_Y3\s*=\s*(\d+)", output)
        errors_Y3 = int(mismatches.group(1)) if mismatches else 0
        total_errors = errors_Y1 + errors_Y3

        if total_errors > 0:
            return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": f"Errors found: {total_errors}"}
        else:
            return {"accuracy": 1.0, "line_count": len(code.splitlines()), "combined_score": 1.0, "error": None}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "test"], check=False)
        except:
            pass