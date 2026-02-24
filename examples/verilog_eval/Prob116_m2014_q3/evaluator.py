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
        code: The Verilog code to evaluate.

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

        # Parse the output
        output = vvp_result.stdout
        line_count = len(output.splitlines())

        accuracy = 1.0
        errors = 0
        errors_f = 0

        if "FAIL" in output:
            accuracy = 0.0
        else:
            # Look for mismatch counts
            mismatch_match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatch_match:
                errors = int(mismatch_match.group(1))
                total_samples = int(mismatch_match.group(2))
                accuracy = 1.0 - (errors / total_samples)
            
            mismatch_match_f = re.search(r"errors_f = (\d+)", output)
            if mismatch_match_f:
                errors_f = int(mismatch_match_f.group(1))
                if errors_f > 0:
                    accuracy = 0.0

        combined_score = accuracy  # Simplest combined score, can be more sophisticated
        
        return {"accuracy": accuracy, "line_count": line_count, "combined_score": combined_score, "error": ""}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "exec"], check=False)
        except:
            pass