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
    Evaluates a Verilog module by running it through iverilog and vvp.

    Args:
        code: The Verilog code of the module to evaluate.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        # Write the code to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "test_exec", "candidate.sv", "testbench.sv", "ref.sv"],
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

        # Parse the simulation output
        output = simulation_result.stdout
        line_count = len(output.splitlines())

        accuracy = 1.0
        error = None

        if "FAIL" in output:
            accuracy = 0.0
        else:
            # Parse for mismatch counts
            match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if match:
                errors = int(match.group(1))
                clocks = int(match.group(2))
                if errors > 0:
                    accuracy = 1.0 - (float(errors) / clocks)
            elif "TIMEOUT" in output:
                accuracy = 0.0
            elif "errors" in output:
                match_errors = re.search(r"stats1\.errors: (\d+)", output)
                match_clocks = re.search(r"stats1\.clocks: (\d+)", output)
                if match_errors and match_clocks:
                    errors = int(match_errors.group(1))
                    clocks = int(match_clocks.group(1))
                    if errors > 0:
                        accuracy = 1.0 - (float(errors) / clocks)

        combined_score = accuracy  # For simplicity, use accuracy as combined score

        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": combined_score,
            "error": error
        }

    except subprocess.CalledProcessError as e:
        return {
            "accuracy": 0.0,
            "line_count": 0,
            "combined_score": 0.0,
            "error": str(e)
        }
    except Exception as e:
        return {
            "accuracy": 0.0,
            "line_count": 0,
            "combined_score": 0.0,
            "error": str(e)
        }
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "-f", "candidate.sv", "test_exec", "testbench.sv", "ref.sv"], check=False)
        except:
            pass