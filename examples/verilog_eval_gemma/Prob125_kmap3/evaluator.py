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
    Evaluates a Verilog module by running it against a testbench and analyzing the output.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results:
            - accuracy: The accuracy score (float).
            - line_count: The number of lines in the Verilog code (int).
            - combined_score: A combined score based on accuracy and line count (float).
            - error: An error message if any occurred during the process (str), otherwise None.
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

        # Run the simulation
        vvp_cmd = ["vvp", "exec"]
        vvp_result = subprocess.run(vvp_cmd, capture_output=True, text=True)
        output = vvp_result.stdout

        # Parse the output
        if "FAIL" in output:
            accuracy = 0.0
            mismatches_match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches_match:
                errors = int(mismatches_match.group(1))
                clocks = int(mismatches_match.group(2))
                accuracy = 1.0 - (errors / clocks) if clocks > 0 else 0.0
            else:
                accuracy = 0.0

        elif "PASS" in output:
            accuracy = 1.0
        else:
            mismatches_match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches_match:
                errors = int(mismatches_match.group(1))
                clocks = int(mismatches_match.group(2))
                accuracy = 1.0 - (errors / clocks) if clocks > 0 else 1.0
            else:
                accuracy = 1.0

        line_count = len(code.splitlines())
        combined_score = accuracy * (1.0 / line_count) if line_count > 0 else accuracy

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": combined_score, "error": None}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "exec"], check=False)
        except:
            pass