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
    Evaluates a Verilog module by running it against a reference model using Iverilog.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results:
        - accuracy: The accuracy of the module (float between 0.0 and 1.0).
        - line_count: The number of lines in the Verilog code.
        - combined_score: A combined score based on accuracy and line count (not implemented).
        - error: An error message if any occurred during the evaluation (string, or None if no error).
    """

    try:
        # Write the candidate module to a file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run Iverilog
        iverilog_cmd = f"iverilog -g2012 -o test_exec candidate.sv testbench.sv ref.sv"
        iverilog_result = subprocess.run(iverilog_cmd, shell=True, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": 0,
                "combined_score": 0.0,
                "error": f"Iverilog compilation error: {iverilog_result.stderr}"
            }

        # Run the simulation
        vvp_cmd = "./test_exec"
        vvp_result = subprocess.run(vvp_cmd, shell=True, capture_output=True, text=True)

        # Parse the simulation output
        output = vvp_result.stdout
        
        # Check for "FAIL"
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches:\s*(\d+)\s*in\s*(\d+)", output)
            if mismatches:
                mismatches_count = int(mismatches.group(1))
                total_count = int(mismatches.group(2))
                accuracy = 1.0 - (float(mismatches_count) / float(total_count))
            else:
                accuracy = 0.0
        
        # Check for "PASS"
        elif "PASS" in output:
            accuracy = 1.0
        
        # Check for error counts
        else:
            error_counts = {}
            for line in output.splitlines():
                match = re.search(r"stats1\.errors_out_(\w+)\s*=\s*(\d+)", line)
                if match:
                    signal = match.group(1)
                    count = int(match.group(2))
                    error_counts[signal] = count
            
            total_errors = sum(error_counts.values())
            if total_errors == 0:
                accuracy = 1.0
            else:
                # Calculate accuracy based on total errors (example)
                total_signals = len(error_counts)
                accuracy = 1.0 - (float(total_errors) / float(total_signals)) if total_signals > 0 else 0.0
            
        # Calculate line count
        line_count = len(code.splitlines())

        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": 1.0,  # Placeholder - not implemented
            "error": None
        }

    except Exception as e:
        return {
            "accuracy": 0.0,
            "line_count": 0,
            "combined_score": 0.0,
            "error": str(e)
        }

    finally:
        # Clean up files
        try:
            subprocess.run("rm -f candidate.sv test_exec", shell=True)
        except:
            pass