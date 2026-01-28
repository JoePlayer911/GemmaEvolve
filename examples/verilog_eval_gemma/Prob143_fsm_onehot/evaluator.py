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
        - line_count: The number of lines in the candidate Verilog code.
        - combined_score: A combined score (e.g., accuracy * line_count).
        - error: A string containing any error messages encountered during the evaluation.
    """

    exec_name = "eval_exec"
    candidate_file = "candidate.sv"
    testbench_file = "testbench.sv"
    ref_file = "ref.sv"

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
                "line_count": 0,
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

        # Check for FAIL
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches:\s*(\d+)\s*in\s*(\d+)", output)
            if mismatches:
                mismatches_count = int(mismatches.group(1))
                total_count = int(mismatches.group(2))
                accuracy = 1.0 - (float(mismatches_count) / float(total_count))
            else:
                accuracy = 0.0
        # Check for PASS
        elif "PASS" in output:
            accuracy = 1.0
        # Check for errors based on stats
        else:
            errors_next_state = int(re.search(r"stats1\.errors_next_state\s*=\s*(\d+)", output).group(1)) if re.search(r"stats1\.errors_next_state\s*=\s*(\d+)", output) else 0
            errors_out1 = int(re.search(r"stats1\.errors_out1\s*=\s*(\d+)", output).group(1)) if re.search(r"stats1\.errors_out1\s*=\s*(\d+)", output) else 0
            errors_out2 = int(re.search(r"stats1\.errors_out2\s*=\s*(\d+)", output).group(1)) if re.search(r"stats1\.errors_out2\s*=\s*(\d+)", output) else 0
            total_errors = errors_next_state + errors_out1 + errors_out2
            if total_errors == 0:
                accuracy = 1.0
            else:
                accuracy = 1.0 - (float(total_errors) / 100)  # Assuming 100 is a reasonable total count
                

        line_count = len(code.splitlines())
        combined_score = accuracy * line_count
        
        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": combined_score,
            "error": ""
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
        import os
        try:
            os.remove(candidate_file)
            os.remove(exec_name)
        except FileNotFoundError:
            pass