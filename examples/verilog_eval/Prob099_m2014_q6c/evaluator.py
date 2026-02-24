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
        # Write the candidate code to a file
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

        # Parse the output
        output = vvp_result.stdout
        line_count = len(code.splitlines())

        if "FAIL" in output:
            mismatches = re.search(r"Mismatches:\s*(\d+)\s*in\s*(\w+)", output)
            if mismatches:
                count = int(mismatches.group(1))
                signal = mismatches.group(2)
                accuracy = 1.0 - (count / 1000.0)  # Example scoring
                return {"accuracy": accuracy, "line_count": line_count, "combined_score": accuracy, "error": ""}
            else:
                return {"accuracy": 0.0, "line_count": line_count, "combined_score": 0.0, "error": ""}

        if "PASS" in output:
            return {"accuracy": 1.0, "line_count": line_count, "combined_score": 1.0, "error": ""}

        # Check for errors in the simulation output
        errors = re.search(r"stats1\.errors\s*=\s*(\d+)", output)
        if errors:
            error_count = int(errors.group(1))
            if error_count == 0:
                return {"accuracy": 1.0, "line_count": line_count, "combined_score": 1.0, "error": ""}
            else:
                return {"accuracy": 1.0 - (error_count / 1000.0), "line_count": line_count, "combined_score": 1.0 - (error_count / 1000.0), "error": ""}
        
        return {"accuracy": 1.0, "line_count": line_count, "combined_score": 1.0, "error": ""}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up the generated files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "exec"], check=False)
        except:
            pass