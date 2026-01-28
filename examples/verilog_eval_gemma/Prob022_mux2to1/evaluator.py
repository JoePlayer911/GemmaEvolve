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
    Evaluates a Verilog module by simulating it against a reference module
    using Iverilog and VVP.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the accuracy, line count, combined score, and error.
    """
    exec_name = "a.out"
    try:
        # Write the candidate module to a file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", exec_name, "candidate.sv", "testbench.sv", "ref.sv"],
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
        sim_result = subprocess.run(
            [exec_name], capture_output=True, text=True
        )

        # Parse the simulation output
        output = sim_result.stdout
        accuracy = 1.0
        errors = 0
        mismatches = 0

        if "FAIL" in output:
            accuracy = 0.0

        # Parse mismatch counts
        match = re.search(r"Mismatches: (\d+) in (\d+)", output)
        if match:
            errors = int(match.group(1))
            mismatches = int(match.group(2))

        if "TIMEOUT" in output:
            accuracy = 0.0

        if errors == 0 and "FAIL" not in output:
            accuracy = 1.0
        elif errors > 0:
            accuracy = 1.0 - (errors / mismatches) if mismatches > 0 else 0.0

        # Calculate line count
        line_count = len(code.splitlines())

        # Calculate combined score (simple accuracy for now)
        combined_score = accuracy

        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": combined_score,
            "error": "",
        }

    except Exception as e:
        return {
            "accuracy": 0.0,
            "line_count": len(code.splitlines()),
            "combined_score": 0.0,
            "error": str(e),
        }
    finally:
        # Clean up the executable file
        try:
            subprocess.run(["rm", "-f", "candidate.sv", exec_name], check=False)
        except:
            pass