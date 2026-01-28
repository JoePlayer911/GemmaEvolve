import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it against a testbench and analyzing the output.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results:
        - accuracy: The accuracy score (float).
        - line_count: The number of lines in the Verilog code (int).
        - combined_score: A combined score based on accuracy and line count (float).
        - error: An error message if any occurred during evaluation (str).
    """

    try:
        # Save the candidate code to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run iverilog
        iverilog_cmd = ["iverilog", "-g2012", "-o", "simulation", "candidate.sv", "testbench.sv", "ref.sv"]
        iverilog_result = subprocess.run(iverilog_cmd, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run vvp
        vvp_result = subprocess.run(["vvp", "simulation"], capture_output=True, text=True)

        # Analyze the output
        output = vvp_result.stdout
        line_count = len(code.splitlines())

        accuracy = 1.0
        errors = 0
        mismatches = 0
        
        if "FAIL" in output:
            accuracy = 0.0
        else:
            # Parse mismatch counts
            match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if match:
                mismatches = int(match.group(1))
                total_samples = int(match.group(2))
                if total_samples > 0:
                    accuracy = 1.0 - (float(mismatches) / total_samples)
                else:
                    accuracy = 1.0  # Handle case where total_samples is zero

            # Check for errors explicitly
            if "errors:" in output:
              match = re.search(r"errors: (\d+)", output)
              if match:
                errors = int(match.group(1))
                if errors > 0:
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
            os.remove("candidate.sv")
            os.remove("simulation")
        except FileNotFoundError:
            pass  # Ignore if files don't exist