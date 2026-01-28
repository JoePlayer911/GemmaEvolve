import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it through iverilog and vvp,
    then analyzing the simulation output.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results:
            - accuracy: The accuracy score (float).
            - line_count: The number of lines in the code (int).
            - combined_score: The combined score (float).
            - error: An error message (str), or None if no error occurred.
    """

    try:
        # Write the code to a temporary file
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

        output = simulation_result.stdout

        # Parse the output for mismatches
        mismatch_pattern = re.compile(r"Mismatches: (\d+) in (\d+)")
        match = mismatch_pattern.search(output)
        errors = 0
        clocks = 0
        if match:
            errors = int(match.group(1))
            clocks = int(match.group(2))
        
        # Check for "FAIL" or "PASS"
        if "FAIL" in output:
            if errors > 0:
                accuracy = 0.0
            else:
                accuracy = 0.0  # Fail even with no mismatches if FAIL is present
        elif "PASS" in output:
            accuracy = 1.0
        else:
            if errors == 0:
                accuracy = 1.0
            else:
                accuracy = 1.0 - (errors / clocks) if clocks > 0 else 0.0

        # Calculate line count
        line_count = len(code.splitlines())
        combined_score = accuracy * line_count

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
            os.remove("candidate.sv")
            os.remove("test_exec")
        except FileNotFoundError:
            pass