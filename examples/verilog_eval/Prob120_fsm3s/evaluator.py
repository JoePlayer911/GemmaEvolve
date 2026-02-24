import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it through iverilog and vvp,
    then parsing the simulation output to determine accuracy.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing:
            - accuracy: The calculated accuracy (float).
            - line_count: The number of lines in the candidate code (int).
            - combined_score: A combined score based on accuracy and line count (float).
            - error: An error message if any occurred during the process (str).
    """
    try:
        exec_name = "test_exec"  # Name of the executable
        candidate_file = "candidate.sv"
        ref_file = "ref.sv"

        # Write the candidate code to a file
        with open(candidate_file, "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_command = f"iverilog -g2012 -o {exec_name} {candidate_file} {ref_file}"
        compile_result = subprocess.run(compile_command, shell=True, capture_output=True, text=True)

        if compile_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": 0,
                "combined_score": 0.0,
                "error": f"Compilation error: {compile_result.stderr}"
            }

        # Run the simulation
        simulation_command = f"./{exec_name}"
        simulation_result = subprocess.run(simulation_command, shell=True, capture_output=True, text=True)

        # Parse the simulation output
        output = simulation_result.stdout
        accuracy = 1.0
        errors = 0
        clocks = 0
        errors_out = 0

        if "FAIL" in output:
            accuracy = 0.0
        else:
            # Attempt to parse mismatch counts
            match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if match:
                errors = int(match.group(1))
                clocks = int(match.group(2))
            
            match_out = re.search(r"errors_out = (\d+)", output)
            if match_out:
                errors_out = int(match_out.group(1))

            if errors > 0:
                accuracy = 1.0 - (float(errors) / clocks) if clocks > 0 else 0.0

        line_count = len(code.splitlines())
        combined_score = accuracy * (1.0 / line_count) if line_count > 0 else 0.0

        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": combined_score,
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
        # Clean up temporary files
        import os
        try:
            os.remove(candidate_file)
            os.remove(ref_file)
            if os.path.exists(exec_name):
                os.remove(exec_name)
        except OSError:
            pass