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
    Evaluates a Verilog module by running it through Icarus Verilog and a testbench.

    Args:
        code: The Verilog code of the module to evaluate.

    Returns:
        A dictionary containing the evaluation results:
            accuracy: The accuracy score (float).
            line_count: The number of lines in the code (int).
            combined_score: A combined score based on accuracy and line count (float).
            error: An error message if any occurred during evaluation (str), otherwise None.
    """

    try:
        # Save the candidate code to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code using Icarus Verilog
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "simulation", "candidate.sv", "testbench.sv", "ref.sv"],
            capture_output=True,
            text=True
        )

        if compile_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": len(code.splitlines()),
                "combined_score": 0.0,
                "error": f"Compilation error: {compile_result.stderr}"
            }

        # Run the simulation using Gnu VVP
        simulation_result = subprocess.run(
            ["vvp", "simulation"],
            capture_output=True,
            text=True
        )

        # Parse the simulation output to determine accuracy
        output = simulation_result.stdout
        
        if "FAIL" in output:
            errors = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if errors:
                mismatches = int(errors.group(1))
                total_samples = int(errors.group(2))
                accuracy = 1.0 - (mismatches / total_samples) if total_samples > 0 else 0.0
            else:
                accuracy = 0.0
        elif "PASS" in output:
            accuracy = 1.0
        else:
            # Attempt to parse mismatch counts from the output
            errors = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if errors:
                mismatches = int(errors.group(1))
                total_samples = int(errors.group(2))
                accuracy = 1.0 - (mismatches / total_samples) if total_samples > 0 else 0.0
            else:
                accuracy = 1.0  # Assume PASS if no errors are reported

        line_count = len(code.splitlines())
        combined_score = accuracy * (1.0 / line_count) if line_count > 0 else 1.0

        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": combined_score,
            "error": None
        }

    except Exception as e:
        return {
            "accuracy": 0.0,
            "line_count": len(code.splitlines()),
            "combined_score": 0.0,
            "error": str(e)
        }
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "simulation"], check=False)
        except:
            pass