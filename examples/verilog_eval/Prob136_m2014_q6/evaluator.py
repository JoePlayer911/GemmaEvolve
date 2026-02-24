import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it through iverilog and vvp,
    parsing the output for mismatches and determining accuracy.
    """
    try:
        exec_name = "a.out"  # Standard executable name for vvp
        candidate_name = "candidate.sv"
        ref_name = "testbench.sv"

        # Write the candidate code to a file
        with open(candidate_name, "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_cmd = f"iverilog -g2012 -o {exec_name} {candidate_name} {ref_name}"
        compile_result = subprocess.run(compile_cmd, capture_output=True, text=True)

        if compile_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": compile_result.stderr}

        # Run the simulation
        sim_cmd = f"./{exec_name}"
        sim_result = subprocess.run(sim_cmd, capture_output=True, text=True)

        # Parse the simulation output
        output = sim_result.stdout
        line_count = len(output.splitlines())
        
        # Check for "FAIL"
        if "FAIL" in output:
            errors = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if errors:
                mismatches = int(errors.group(1))
                total_samples = int(errors.group(2))
                accuracy = 1.0 - (float(mismatches) / float(total_samples))
                return {"accuracy": accuracy, "line_count": line_count, "combined_score": accuracy, "error": ""}
            else:
                return {"accuracy": 0.0, "line_count": line_count, "combined_score": 0.0, "error": ""}

        # Check for "PASS"
        if "PASS" in output:
            return {"accuracy": 1.0, "line_count": line_count, "combined_score": 1.0, "error": ""}

        # Parse mismatch counts if present
        errors = re.search(r"Mismatches: (\d+) in (\d+)", output)
        if errors:
            mismatches = int(errors.group(1))
            total_samples = int(errors.group(2))
            accuracy = 1.0 - (float(mismatches) / float(total_samples))
            return {"accuracy": accuracy, "line_count": line_count, "combined_score": accuracy, "error": ""}

        # If no errors are found
        return {"accuracy": 1.0, "line_count": line_count, "combined_score": 1.0, "error": ""}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up generated files
        import os
        try:
            os.remove(candidate_name)
            os.remove(ref_name)
            os.remove(exec_name)
        except FileNotFoundError:
            pass