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
        A dictionary containing the evaluation results.
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
        error_message = None

        if "FAIL" in output:
            accuracy = 0.0
        else:
            # Parse mismatches
            mismatches_pattern = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches_pattern:
                errors = int(mismatches_pattern.group(1))
                clocks = int(mismatches_pattern.group(2))
                if errors > 0:
                    accuracy = 1.0 - (errors / clocks) if clocks > 0 else 0.0
            elif "TIMEOUT" in output:
                accuracy = 0.0

        if "ERROR" in output or "FATAL" in output:
            accuracy = 0.0
            error_message = output

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": accuracy, "error": error_message}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "exec"], check=False)
        except:
            pass