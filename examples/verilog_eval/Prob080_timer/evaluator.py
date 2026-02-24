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
        code: The Verilog code of the module to evaluate.

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
            return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run vvp
        vvp_cmd = ["vvp", "exec"]
        vvp_result = subprocess.run(vvp_cmd, capture_output=True, text=True)

        # Parse the output
        output = vvp_result.stdout
        line_count = len(code.splitlines())

        if "FAIL" in output:
            accuracy = 0.0
            mismatch_pattern = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatch_pattern:
                errors = int(mismatch_pattern.group(1))
                total_samples = int(mismatch_pattern.group(2))
                accuracy = 1.0 - (errors / total_samples) if total_samples > 0 else 0.0
            else:
                accuracy = 0.0
            return {"accuracy": accuracy, "line_count": line_count, "combined_score": 0.0, "error": "FAIL"}

        if "PASS" in output:
            accuracy = 1.0
            return {"accuracy": accuracy, "line_count": line_count, "combined_score": 1.0, "error": None}

        # Parse mismatch counts if present
        mismatch_pattern = re.search(r"Mismatches: (\d+) in (\d+)", output)
        if mismatch_pattern:
            errors = int(mismatch_pattern.group(1))
            total_samples = int(mismatch_pattern.group(2))
            accuracy = 1.0 - (errors / total_samples) if total_samples > 0 else 0.0
        else:
            accuracy = 1.0  # Assume pass if no mismatches are found

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": accuracy, "error": None}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "exec"], check=False)
        except:
            pass