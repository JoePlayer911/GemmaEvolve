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
        A dictionary with keys: accuracy, line_count, combined_score, error.
    """
    try:
        # Save the candidate code to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "test_exec", "candidate.sv", "testbench.sv", "ref.sv"],
            capture_output=True,
            text=True,
        )

        if compile_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": len(code.splitlines()),
                "combined_score": 0.0,
                "error": compile_result.stderr,
            }

        # Run the simulation
        simulation_result = subprocess.run(
            ["vvp", "test_exec"], capture_output=True, text=True
        )

        # Parse the simulation output
        output = simulation_result.stdout
        line_count = len(code.splitlines())
        accuracy = 1.0
        error_message = None

        if "FAIL" in output:
            accuracy = 0.0

        # Parse mismatch counts
        mismatch_pattern = re.compile(r"Mismatches: (\d+) in (\d+)")
        match = mismatch_pattern.search(output)
        if match:
            errors = int(match.group(1))
            clocks = int(match.group(2))
            if errors > 0:
                accuracy = 1.0 - (float(errors) / clocks) if clocks > 0 else 0.0

        if "TIMEOUT" in output:
            accuracy = 0.0

        if "errors" in output and "clocks" in output:
            errors_pattern = re.compile(r"stats1\.errors = (\d+)")
            clocks_pattern = re.compile(r"stats1\.clocks = (\d+)")
            errors_match = errors_pattern.search(output)
            clocks_match = clocks_pattern.search(output)
            if errors_match and clocks_match:
                errors = int(errors_match.group(1))
                clocks = int(clocks_match.group(1))
                if errors > 0:
                    accuracy = 1.0 - (float(errors) / clocks) if clocks > 0 else 0.0

        if "errors_q" in output:
            errors_q_pattern = re.compile(r"stats1\.errors_q = (\d+)")
            errors_q_match = errors_q_pattern.search(output)
            if errors_q_match:
                errors_q = int(errors_q_match.group(1))
                if errors_q > 0:
                    accuracy = 0.0
        
        if accuracy < 0:
            accuracy = 0.0
        if accuracy > 1:
            accuracy = 1.0

        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": accuracy,
            "error": error_message,
        }

    except Exception as e:
        return {
            "accuracy": 0.0,
            "line_count": len(code.splitlines()),
            "combined_score": 0.0,
            "error": str(e),
        }
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "test_exec"], check=False)
            subprocess.run(["rm", "coredump"], check=False)
        except:
            pass