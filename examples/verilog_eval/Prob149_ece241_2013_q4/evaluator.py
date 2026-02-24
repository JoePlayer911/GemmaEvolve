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
            - accuracy: The accuracy score (float between 0.0 and 1.0).
            - line_count: The number of lines in the Verilog code.
            - combined_score: A combined score (float, can be used for ranking).
            - error: A string containing any error messages.
    """

    exec_name = "eval_exec"
    testbench_file = "testbench.sv"
    ref_file = "ref.sv"
    candidate_file = "candidate.sv"

    try:
        with open(candidate_file, "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", exec_name, candidate_file, testbench_file, ref_file],
            capture_output=True,
            text=True
        )

        if compile_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": len(code.splitlines()),
                "combined_score": 0.0,
                "error": compile_result.stderr
            }

        # Run the simulation
        simulation_result = subprocess.run(
            [exec_name],
            capture_output=True,
            text=True
        )

        output = simulation_result.stdout
        error = simulation_result.stderr

        # Check for explicit mismatch counts
        mismatch_pattern = r"Mismatches:\s*(\d+)\s*in\s*(\d+)"
        mismatch_match = re.search(mismatch_pattern, output)
        mismatches = int(mismatch_match.group(1)) if mismatch_match else 0
        total = int(mismatch_match.group(2)) if mismatch_match else 0
        
        # Check for "FAIL" or "PASS"
        if "FAIL" in output.upper():
            if mismatches > 0:
                accuracy = 0.0
            else:
                accuracy = 0.0
        elif "PASS" in output.upper():
            accuracy = 1.0
        else:
            # Check for errors in the simulation output
            if "error" in output.lower() or "warning" in output.lower():
                accuracy = 0.0
            else:
                accuracy = 1.0

        if mismatches > 0 and total > 0:
            accuracy = 1.0 - (float(mismatches) / total)

        combined_score = accuracy  # Simple combined score, can be adjusted

        return {
            "accuracy": accuracy,
            "line_count": len(code.splitlines()),
            "combined_score": combined_score,
            "error": error
        }

    except Exception as e:
        return {
            "accuracy": 0.0,
            "line_count": len(code.splitlines()),
            "combined_score": 0.0,
            "error": str(e)
        }
    finally:
        # Clean up generated files
        try:
            subprocess.run(["rm", "-f", candidate_file, exec_name], check=False)
        except:
            pass