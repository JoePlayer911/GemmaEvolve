import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it through Iverilog and comparing
    its output to a reference implementation.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results:
            - accuracy: The accuracy score (float between 0.0 and 1.0).
            - line_count: The number of lines in the Verilog code.
            - combined_score: A combined score (not used in this example).
            - error: An error message (if any).
    """
    try:
        exec_name = "eval_exec"
        candidate_file = "candidate.sv"
        testbench_file = "testbench.sv"
        ref_file = "ref.sv"

        with open(candidate_file, "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_cmd = f"iverilog -g2012 -o {exec_name} {candidate_file} {testbench_file} {ref_file}"
        compile_result = subprocess.run(compile_cmd, shell=True, capture_output=True, text=True)

        if compile_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": len(code.splitlines()),
                "combined_score": 0.0,
                "error": f"Compilation error: {compile_result.stderr}"
            }

        # Run the simulation
        sim_cmd = f"./{exec_name}"
        sim_result = subprocess.run(sim_cmd, shell=True, capture_output=True, text=True)

        # Parse the simulation output
        output = sim_result.stdout
        accuracy = 1.0
        errors = 0
        mismatches = 0

        if "FAIL" in output:
            accuracy = 0.0
        else:
            # Attempt to parse mismatch counts
            match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if match:
                errors = int(match.group(1))
                mismatches = int(match.group(2))

            if errors > 0:
                accuracy = 1.0 - (float(errors) / mismatches) if mismatches > 0 else 0.0

            if "PASS" in output:
                accuracy = 1.0

        return {
            "accuracy": accuracy,
            "line_count": len(code.splitlines()),
            "combined_score": 1.0,
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
        # Clean up files
        import os
        try:
            os.remove("candidate.sv")
            os.remove(f"{exec_name}")
            os.remove("testbench.sv")
            os.remove("ref.sv")
        except FileNotFoundError:
            pass