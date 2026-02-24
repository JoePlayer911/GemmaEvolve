import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by simulating it against a reference module.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results:
        - accuracy: The accuracy score (float).
        - line_count: The number of lines in the Verilog code (int).
        - combined_score: A combined score (float).
        - error: An error message (str), or None if no error occurred.
    """
    try:
        exec_name = "eval_exec"  # Name of the executable
        candidate_file = "candidate.sv"
        testbench_file = "testbench.sv"
        ref_file = "ref.sv"

        # Write the candidate code to a file
        with open(candidate_file, "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_cmd = ["iverilog", "-g2012", "-o", exec_name, candidate_file, testbench_file, ref_file]
        compile_result = subprocess.run(compile_cmd, capture_output=True, text=True)

        if compile_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": 0,
                "combined_score": 0.0,
                "error": compile_result.stderr
            }

        # Run the simulation
        simulation_cmd = [exec_name]
        simulation_result = subprocess.run(simulation_cmd, capture_output=True, text=True)

        # Parse the simulation output
        output = simulation_result.stdout
        accuracy = 1.0
        errors = 0
        clocks = 0
        errors_z = 0

        if "FAIL" in output:
            accuracy = 0.0
        else:
            # Attempt to parse mismatch counts
            mismatch_pattern = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatch_pattern:
                errors = int(mismatch_pattern.group(1))
                clocks = int(mismatch_pattern.group(2))
            
            mismatch_pattern_z = re.search(r"errors_z = (\d+)", output)
            if mismatch_pattern_z:
                errors_z = int(mismatch_pattern_z.group(1))


            if errors > 0:
                accuracy = 1.0 - (float(errors) / clocks) if clocks > 0 else 0.0

        if "PASS" in output:
            accuracy = 1.0
        
        combined_score = accuracy  # Simple combined score for now

        return {
            "accuracy": accuracy,
            "line_count": len(code.splitlines()),
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
        # Clean up generated files
        import os
        try:
            os.remove(candidate_file)
            os.remove(testbench_file)
            os.remove(ref_file)
            os.remove(exec_name)
        except FileNotFoundError:
            pass