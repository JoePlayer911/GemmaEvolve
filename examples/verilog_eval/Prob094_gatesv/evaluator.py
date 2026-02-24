import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by simulating it against a reference model.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results:
        - accuracy: The accuracy of the module (float).
        - line_count: The number of lines in the candidate module (int).
        - combined_score: A combined score based on accuracy and line count (float).
        - error: An error message if any occurred during the process (str).
    """
    try:
        # Save the candidate module to a temporary file
        candidate_file = "candidate.sv"
        with open(candidate_file, "w") as f:
            f.write(code)

        # Compile the Verilog code using Iverilog
        compile_cmd = ["iverilog", "-g2012", "-o", "test_exec", candidate_file, "testbench.sv", "ref.sv"]
        compile_result = subprocess.run(compile_cmd, capture_output=True, text=True)

        if compile_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": compile_result.stderr}

        # Run the simulation using VVP
        sim_result = subprocess.run(["vvp", "test_exec"], capture_output=True, text=True)

        # Analyze the simulation output
        output = sim_result.stdout
        line_count = len(code.splitlines())

        if "FAIL" in output:
            mismatches = re.search(r"Mismatches:\s*(\d+)\s*in\s*(\d+)", output)
            if mismatches:
                x = int(mismatches.group(1))
                y = int(mismatches.group(2))
                accuracy = 1.0 - (x / y) if y > 0 else 0.0
            else:
                accuracy = 0.0
        elif "PASS" in output:
            accuracy = 1.0
        else:
            # Check for errors based on the provided example output
            errors_out_both = 0
            errors_out_any = 0
            errors_out_different = 0

            for line in output.splitlines():
                if "stats1.errors_out_both = stats1.errors_out_both+1'b1;" in line:
                    errors_out_both = 1
                if "stats1.errors_out_any = stats1.errors_out_any+1'b1;" in line:
                    errors_out_any = 1
                if "stats1.errors_out_different = stats1.errors_out_different+1'b1;" in line:
                    errors_out_different = 1

            if errors_out_both == 0 and errors_out_any == 0 and errors_out_different == 0:
                accuracy = 1.0
            else:
                accuracy = 0.0

        # Calculate combined score
        combined_score = accuracy * (1.0 / line_count) if line_count > 0 else 0.0

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": combined_score, "error": ""}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        import os
        try:
            os.remove(candidate_file)
            os.remove("test_exec")
        except FileNotFoundError:
            pass