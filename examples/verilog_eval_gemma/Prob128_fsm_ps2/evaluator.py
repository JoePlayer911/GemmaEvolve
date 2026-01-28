import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by simulating it against a reference model using Iverilog and VVP.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results:
            - accuracy: The accuracy score (float between 0.0 and 1.0).
            - line_count: The number of lines in the input code.
            - combined_score:  A combined score (not used in this version).
            - error: An error message if any occurred, otherwise None.
    """

    try:
        exec_name = "eval_result"
        candidate_file = "candidate.sv"
        ref_file = "testbench.sv"

        with open(candidate_file, "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_command = f"iverilog -g2012 -o {exec_name} {candidate_file} {ref_file}"
        compile_result = subprocess.run(compile_command, shell=True, capture_output=True, text=True)

        if compile_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": code.count("\n"),
                "combined_score": 0.0,
                "error": compile_result.stderr
            }

        # Run the simulation
        run_command = f"./{exec_name}"
        run_result = subprocess.run(run_command, shell=True, capture_output=True, text=True)

        output = run_result.stdout

        # Parse the output to determine accuracy
        if "FAIL" in output:
            accuracy = 0.0
            mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches:
                errors = int(mismatches.group(1))
                total_samples = int(mismatches.group(2))
                accuracy = 1.0 - (errors / total_samples) if total_samples > 0 else 0.0
            else:
                accuracy = 0.0
        elif "PASS" in output:
            accuracy = 1.0
        else:
            # Check for mismatch counts
            mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches:
                errors = int(mismatches.group(1))
                total_samples = int(mismatches.group(2))
                accuracy = 1.0 - (errors / total_samples) if total_samples > 0 else 0.0
            else:
                accuracy = 1.0
        
        return {
            "accuracy": accuracy,
            "line_count": code.count("\n"),
            "combined_score": 1.0,
            "error": None
        }

    except Exception as e:
        return {
            "accuracy": 0.0,
            "line_count": code.count("\n"),
            "combined_score": 0.0,
            "error": str(e)
        }
    finally:
        # Clean up the generated files
        import os
        try:
            os.remove(candidate_file)
            os.remove(f"{exec_name}")
        except FileNotFoundError:
            pass