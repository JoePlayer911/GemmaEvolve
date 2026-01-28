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
    Evaluates a Verilog module by simulating it against a reference module using Iverilog and VVP.
    """
    try:
        exec_name = "a.out"  # Temporary executable name
        candidate_name = "candidate.sv"
        ref_name = "testbench.sv"

        # Write the candidate code to a file
        with open(candidate_name, "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_cmd = f"iverilog -g2012 -o {exec_name} {candidate_name} {ref_name}"
        compile_result = subprocess.run(compile_cmd, shell=True, capture_output=True, text=True)

        if compile_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": compile_result.stderr}

        # Run the simulation
        sim_result = subprocess.run(f"./{exec_name}", shell=True, capture_output=True, text=True)
        output = sim_result.stdout

        # Parse the output to determine accuracy
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches:\s*(.*)", output)
            if mismatches:
                mismatch_count = int(mismatches.group(1))
                accuracy = 1.0 - (mismatch_count / 1000.0)  # Assuming 1000 cycles
            else:
                accuracy = 0.0
        elif "PASS" in output:
            accuracy = 1.0
        else:
            # Check for errors based on the provided code snippet logic
            errors_out_byte = re.search(r"stats1\.errors_out_byte = (\d+)", output)
            errors_done = re.search(r"stats1\.errors_done = (\d+)", output)

            if errors_out_byte and errors_done:
                errors_out_byte = int(errors_out_byte.group(1))
                errors_done = int(errors_done.group(1))
                if errors_out_byte == 0 and errors_done == 0:
                    accuracy = 1.0
                else:
                    accuracy = 0.0
            else:
                accuracy = 1.0

        # Get line count of the candidate code
        line_count = code.count('\n') + 1

        # Combined score (simple average of accuracy and line count)
        combined_score = (accuracy + line_count / 100.0) / 2.0

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": combined_score, "error": ""}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run(f"rm {candidate_name}", shell=True)
            subprocess.run(f"rm {exec_name}", shell=True)
        except:
            pass