import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it against a testbench.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results:
            accuracy: The accuracy of the module (float).
            line_count: The number of lines in the code (int).
            combined_score: A combined score based on accuracy and line count (float).
            error: An error message if any occurred during the process (str), otherwise None.
    """
    try:
        # Save the candidate module to a file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "test", "candidate.sv", "testbench.sv", "ref.sv"],
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
        sim_result = subprocess.run(
            ["vvp", "test"],
            capture_output=True,
            text=True
        )

        # Analyze the simulation output
        output = sim_result.stdout
        line_count = len(code.splitlines())

        if "FAIL" in output:
            mismatches = re.search(r"Mismatches: (.*)", output)
            if mismatches:
                accuracy = 0.0
            else:
                accuracy = 0.0
        elif "PASS" in output or "errors" not in output:
            accuracy = 1.0
        else:
            # Parse error counts from output
            errors_match = re.search(r"stats1\.errors = (\d+)", output)
            if errors_match:
                errors = int(errors_match.group(1))
                if errors == 0:
                    accuracy = 1.0
                else:
                    accuracy = 1.0 - (errors / 100.0)  # Example scaling
            else:
                accuracy = 0.0

        # Calculate combined score
        combined_score = accuracy * (1.0 / (line_count / 100.0))  # Normalize by line count

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
        # Clean up the generated files
        import os
        try:
            os.remove("candidate.sv")
            os.remove("test")
        except FileNotFoundError:
            pass