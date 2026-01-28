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
    Evaluates a Verilog module by simulating it against a reference module.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results:
            - accuracy: The accuracy score (float).
            - line_count: The number of lines in the Verilog code (int).
            - combined_score: A combined score based on accuracy and line count (float).
            - error: An error message if any occurred (str).
    """

    try:
        # Create a temporary file for the candidate module
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "test_exec", "candidate.sv", "testbench.sv", "ref.sv"],
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
            ["vvp", "test_exec"],
            capture_output=True,
            text=True
        )

        # Parse the simulation output
        output = simulation_result.stdout
        accuracy = 1.0
        errors = 0
        mismatches = 0
        errors_out = 0
        
        if "FAIL" in output:
            accuracy = 0.0
        else:
            # Attempt to parse mismatch counts
            mismatch_pattern = r"Mismatches: (\d+) in (\d+)"
            match = re.search(mismatch_pattern, output)
            if match:
                errors = int(match.group(1))
                mismatches = int(match.group(2))
            
            errors_out_pattern = r"stats\.errors_out = (\d+)"
            match_out = re.search(errors_out_pattern, output)
            if match_out:
                errors_out = int(match_out.group(1))
            
            if errors > 0 or mismatches > 0 or errors_out > 0:
                accuracy = 1.0 - (float(errors + mismatches + errors_out) / float(mismatches if mismatches > 0 else 1)) #Avoid division by zero if no mismatches

        if "TIMEOUT" in output:
            accuracy = 0.0

        # Calculate the combined score
        line_count = len(code.splitlines())
        combined_score = accuracy * (1.0 / line_count) if line_count > 0 else 0.0

        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": combined_score,
            "error": ""
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
            subprocess.run(["rm", "test_exec"], check=False)
            subprocess.run(["rm", "core.vcd"], check=False)
        except:
            pass