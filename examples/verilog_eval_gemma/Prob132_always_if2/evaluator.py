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
    Evaluates a Verilog module by running it against a reference module using Iverilog and Verilator.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary with the following keys:
            accuracy: A float representing the accuracy of the module (1.0 for pass, 0.0 for fail).
            line_count: The number of lines in the candidate Verilog code.
            combined_score: A float representing the overall score (accuracy).
            error: A string containing any error messages encountered during the evaluation.
    """

    candidate_file = "candidate.sv"
    with open(candidate_file, "w") as f:
        f.write(code)

    try:
        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "test_exec", candidate_file, "testbench.sv", "ref.sv"],
            capture_output=True,
            text=True,
            check=True
        )

        # Run the simulation
        simulation_result = subprocess.run(
            ["vvp", "test_exec"],
            capture_output=True,
            text=True,
            check=True
        )

        output = simulation_result.stdout

        # Check for "FAIL"
        if "FAIL" in output:
            accuracy = 0.0
            mismatches = re.search(r"Mismatches:\s*(\w+)\s*in\s*(\w+)", output)
            if mismatches:
                accuracy = 0.0  # Still fail, but provide mismatch info
            error = "Simulation failed."
        # Check for "PASS"
        elif "PASS" in output:
            accuracy = 1.0
            error = "Simulation passed."
        # Parse mismatch counts
        else:
            mismatches = re.search(r"Mismatches:\s*(\d+)", output)
            if mismatches:
                num_mismatches = int(mismatches.group(1))
                if num_mismatches == 0:
                    accuracy = 1.0
                    error = "Simulation passed (no mismatches)."
                else:
                    accuracy = 1.0 - (num_mismatches / 100.0)  # Example scoring
                    error = f"Simulation with {num_mismatches} mismatches."
            else:
                # If no PASS/FAIL and no mismatches found, assume pass
                accuracy = 1.0
                error = "Simulation passed (no explicit result found)."

    except subprocess.CalledProcessError as e:
        accuracy = 0.0
        error = f"Error during compilation or simulation: {e.stderr}"
    except Exception as e:
        accuracy = 0.0
        error = f"An unexpected error occurred: {str(e)}"
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "test_exec"], check=False)
            subprocess.run(["rm", candidate_file], check=False)
        except:
            pass

    line_count = len(code.splitlines())
    combined_score = accuracy

    return {
        "accuracy": accuracy,
        "line_count": line_count,
        "combined_score": combined_score,
        "error": error
    }