import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by simulating it against a reference model using Iverilog and VVP.

    Args:
        code (str): The Verilog code of the module to be evaluated.

    Returns:
        dict: A dictionary containing the evaluation results.
              Keys: 'accuracy', 'line_count', 'combined_score', 'error'.
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

        # Parse the simulation output
        output = simulation_result.stdout
        line_count = len(code.splitlines())

        if "FAIL" in output:
            accuracy = 0.0
            mismatch_pattern = r"Mismatches: (\d+) in (\d+)"
            mismatch_match = re.search(mismatch_pattern, output)
            if mismatch_match:
                errors = int(mismatch_match.group(1))
                clocks = int(mismatch_match.group(2))
                accuracy = 1.0 - (errors / clocks) if clocks > 0 else 0.0
            return {
                "accuracy": accuracy,
                "line_count": line_count,
                "combined_score": accuracy,
                "error": ""
            }

        if "PASS" in output:
            accuracy = 1.0
        else:
            # Parse mismatch counts
            mismatch_pattern = r"Mismatches: (\d+) in (\d+)"
            mismatch_match = re.search(mismatch_pattern, output)
            if mismatch_match:
                errors = int(mismatch_match.group(1))
                clocks = int(mismatch_match.group(2))
                accuracy = 1.0 - (errors / clocks) if clocks > 0 else 0.0
            else:
                accuracy = 1.0

        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": accuracy,
            "error": ""
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
        try:
            import os
            os.remove("candidate.sv")
            os.remove("test_exec")
        except FileNotFoundError:
            pass

if __name__ == '__main__':
    # Example usage:
    verilog_code = """
    module my_module (
      input clk,
      input rst,
      input in,
      output out
    );

    always @(posedge clk) begin
      if (rst)
        out <= 0;
      else
        out <= in;
    end

    endmodule
    """

    result = evaluate(verilog_code)
    print(result)