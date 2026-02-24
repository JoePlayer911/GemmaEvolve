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
    Evaluates a Verilog module by running it through a simulation.

    Args:
        code: The Verilog code to evaluate.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        # Create a temporary Verilog file
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

        if "FAIL" in output:
            accuracy = 0.0
            mismatch_pattern = r"Mismatches: (\d+) in (\d+)"
            mismatch_match = re.search(mismatch_pattern, output)
            if mismatch_match:
                accuracy = 1.0 - (int(mismatch_match.group(1)) / int(mismatch_match.group(2)))
            return {"accuracy": accuracy, "line_count": 0, "combined_score": 0.0, "error": ""}
        
        if "PASS" in output:
            accuracy = 1.0
        else:
            # Extract mismatch information
            mismatch_pattern = r"Mismatches: (\d+) in (\d+)"
            mismatch_match = re.search(mismatch_pattern, output)

            if mismatch_match:
                errors = int(mismatch_match.group(1))
                clocks = int(mismatch_match.group(2))
                accuracy = 1.0 - (errors / clocks) if clocks > 0 else 1.0
            else:
                accuracy = 1.0
                
        line_count = len(code.splitlines())
        combined_score = accuracy  # Simple combined score for now
        
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