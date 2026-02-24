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
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        # Write the code to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run iverilog
        iverilog_cmd = ["iverilog", "-g2012", "-o", "exec", "candidate.sv", "testbench.sv", "ref.sv"]
        iverilog_result = subprocess.run(iverilog_cmd, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run vvp
        vvp_cmd = ["vvp", "exec"]
        vvp_result = subprocess.run(vvp_cmd, capture_output=True, text=True)

        # Parse the output for mismatches or FAIL/PASS
        output = vvp_result.stdout
        
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches:\s*(\d+)\s*in\s*(\d+)", output)
            if mismatches:
                mismatches_count = int(mismatches.group(1))
                total_count = int(mismatches.group(2))
                accuracy = 1.0 - (float(mismatches_count) / float(total_count))
                return {"accuracy": accuracy, "line_count": 0, "combined_score": accuracy, "error": ""}
            else:
                return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": ""}
        
        if "PASS" in output:
            return {"accuracy": 1.0, "line_count": 0, "combined_score": 1.0, "error": ""}

        # Check for errors based on the specific output format
        error_lines = [line for line in output.splitlines() if "stats1.errors" in line and "++" in line]
        if error_lines:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": "Errors found in simulation output."}
        
        return {"accuracy": 1.0, "line_count": 0, "combined_score": 1.0, "error": ""}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "exec"], check=False)
        except:
            pass