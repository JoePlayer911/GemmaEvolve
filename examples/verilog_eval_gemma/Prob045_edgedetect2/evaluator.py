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
    Evaluates a Verilog module using iverilog and vvp.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        # Create a temporary file for the candidate module
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run iverilog
        iverilog_cmd = ["iverilog", "-g2012", "-o", "exec", "candidate.sv", "testbench.sv", "ref.sv"]
        iverilog_result = subprocess.run(iverilog_cmd, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run vvp
        vvp_cmd = ["vvp", "exec"]
        vvp_result = subprocess.run(vvp_cmd, capture_output=True, text=True)

        # Parse the output for mismatches
        output = vvp_result.stdout
        errors = 0
        clocks = 0
        errors_anyedge = 0

        match_errors = re.search(r"Mismatches: (\d+) in (\d+)", output)
        match_errors_anyedge = re.search(r"Mismatches_anyedge: (\d+) in (\d+)", output)

        if match_errors:
            errors = int(match_errors.group(1))
            clocks = int(match_errors.group(2))
        if match_errors_anyedge:
            errors_anyedge = int(match_errors_anyedge.group(1))
            
        # Check for FAIL or PASS
        if "FAIL" in output:
            if errors > 0:
                accuracy = 0.0
            else:
                accuracy = 0.0
        elif "PASS" in output:
            accuracy = 1.0
        else:
            if errors == 0 and errors_anyedge == 0:
                accuracy = 1.0
            else:
                accuracy = 1.0 - (errors / clocks) if clocks > 0 else 1.0

        # Calculate combined score (simple accuracy for now)
        combined_score = accuracy

        return {"accuracy": accuracy, "line_count": len(code.splitlines()), "combined_score": combined_score, "error": ""}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "exec"], check=False)
        except:
            pass