import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it against a testbench and analyzing the output.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        exec_name = "eval_temp"  # Temporary executable name
        candidate_file = "candidate.sv"
        ref_file = "testbench.sv"
        
        with open(candidate_file, "w") as f:
            f.write(code)
        
        # Run iverilog
        iverilog_cmd = f"iverilog -g2012 -o {exec_name} {candidate_file} {ref_file}"
        iverilog_result = subprocess.run(iverilog_cmd, shell=True, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run vvp
        vvp_cmd = f"./{exec_name}"
        vvp_result = subprocess.run(vvp_cmd, shell=True, capture_output=True, text=True)

        output = vvp_result.stdout
        
        # Check for explicit mismatch counts
        mismatch_pattern = r"Mismatches:\s*(\d+)\s*in\s*(\d+)"
        match = re.search(mismatch_pattern, output)
        if match:
            mismatches = int(match.group(1))
            total = int(match.group(2))
            accuracy = 1.0 - (float(mismatches) / float(total))
        else:
            # Check for FAIL/PASS keywords
            if "FAIL" in output:
                accuracy = 0.0
            elif "PASS" in output:
                accuracy = 1.0
            else:
                # Attempt to parse error counts from the output
                error_pattern = r"stats1\.errors_(\w+)"
                error_counts = {}
                for match in re.finditer(error_pattern, output):
                    signal = match.group(1)
                    error_line = output.splitlines()[output.find(match.group(0)):]
                    error_count_pattern = r"stats1\.errors_" + re.escape(signal) + r"\s*=\s*(\d+)"
                    error_count_match = re.search(error_count_pattern, output)
                    if error_count_match:
                        error_counts[signal] = int(error_count_match.group(1))
                
                total_errors = sum(error_counts.values())
                if total_errors == 0:
                    accuracy = 1.0
                else:
                    accuracy = 1.0 - (float(total_errors) / 100) # arbitrary total
        
        line_count = len(code.splitlines())
        combined_score = accuracy # simple score
        
        return {"accuracy": accuracy, "line_count": line_count, "combined_score": combined_score, "error": ""}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        import os
        try:
            os.remove(candidate_file)
            os.remove(f"{exec_name}")
        except FileNotFoundError:
            pass