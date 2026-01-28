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
        A dictionary containing the accuracy, line count, combined score, and error message.
    """
    try:
        # Create a temporary Verilog file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run iverilog
        iverilog_cmd = ["iverilog", "-g2012", "-o", "exec", "candidate.sv", "testbench.sv", "ref.sv"]
        iverilog_result = subprocess.run(iverilog_cmd, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run vvp
        vvp_result = subprocess.run(["vvp", "exec"], capture_output=True, text=True)

        # Parse the output
        output = vvp_result.stdout
        
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches:
                errors = int(mismatches.group(1))
                total_samples = int(mismatches.group(2))
                accuracy = 1.0 - (errors / total_samples) if total_samples > 0 else 0.0
            else:
                accuracy = 0.0
        elif "PASS" in output:
            accuracy = 1.0
        else:
            mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches:
                errors = int(mismatches.group(1))
                total_samples = int(mismatches.group(2))
                accuracy = 1.0 - (errors / total_samples) if total_samples > 0 else 0.0
            else:
                accuracy = 1.0  # Assume pass if no mismatches are reported

        line_count = len(code.splitlines())
        combined_score = accuracy # Simplest combined score

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": combined_score, "error": None}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "exec"], check=False)
        except:
            pass
        try:
            subprocess.run(["rm", "testbench.sv"], check=False)
        except:
            pass
        try:
            subprocess.run(["rm", "ref.sv"], check=False)
        except:
            pass