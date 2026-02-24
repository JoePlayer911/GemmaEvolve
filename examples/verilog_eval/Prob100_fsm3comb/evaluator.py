import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by simulating it against a reference model using Icarus Verilog.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results:
        - accuracy: The accuracy of the module (float).
        - line_count: The number of lines in the candidate code (int).
        - combined_score: A combined score based on accuracy and line count (float).
        - error: An error message if any occurred during evaluation (str), otherwise None.
    """

    try:
        # Create a temporary file for the candidate module
        candidate_file = "candidate.sv"
        with open(candidate_file, "w") as f:
            f.write(code)

        # Compile the Verilog code using Icarus Verilog
        compile_command = f"iverilog -g2012 -o test candidate.sv testbench.sv ref.sv"
        compile_result = subprocess.run(compile_command, shell=True, capture_output=True, text=True)

        if compile_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": len(code.splitlines()),
                "combined_score": 0.0,
                "error": f"Compilation error: {compile_result.stderr}"
            }

        # Run the simulation using Icarus Verilog
        simulation_command = "./test"
        simulation_result = subprocess.run(simulation_command, shell=True, capture_output=True, text=True)

        # Analyze the simulation output
        output = simulation_result.stdout
        line_count = len(code.splitlines())

        if "FAIL" in output:
            mismatches = re.search(r"Mismatches: (.*)", output)
            if mismatches:
                accuracy = 0.0
            else:
                accuracy = 0.0
        elif "PASS" in output:
            accuracy = 1.0
        else:
            # Check for errors reported by the testbench
            error_pattern = r"stats1\.errors = (\d+)"
            errors_match = re.search(error_pattern, output)
            if errors_match:
                errors = int(errors_match.group(1))
                if errors == 0:
                    accuracy = 1.0
                else:
                    accuracy = 0.0
            else:
                accuracy = 1.0  # Assume pass if no errors found

        combined_score = accuracy * (1.0 / line_count)  # Normalize by line count

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
        import os
        try:
            os.remove(candidate_file)
            os.remove("test")
        except FileNotFoundError:
            pass