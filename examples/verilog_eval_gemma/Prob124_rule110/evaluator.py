import os
import subprocess
import re
import tempfile
import logging

logger = logging.getLogger(__name__)

import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it through Iverilog and comparing
    its output against a reference design.

    Args:
        code (str): The Verilog code to be evaluated.

    Returns:
        dict: A dictionary containing the evaluation results, including accuracy,
              line count, combined score, and any error messages.
    """
    try:
        # Write the code to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code using Iverilog
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "exec", "candidate.sv", "testbench.sv", "ref.sv"],
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

        # Run the simulation using vvp
        sim_result = subprocess.run(
            ["vvp", "exec"],
            capture_output=True,
            text=True
        )

        # Parse the simulation output to determine accuracy
        output = sim_result.stdout
        accuracy = 1.0  # Assume pass unless otherwise determined
        errors = 0
        mismatches = 0

        if "FAIL" in output:
            accuracy = 0.0

        # Parse mismatch counts
        match = re.search(r"Mismatches: (\d+) in (\d+)", output)
        if match:
            errors = int(match.group(1))
            mismatches = int(match.group(2))
        
        if "TIMEOUT" in output:
            accuracy = 0.0
        
        if errors == 0 and "Mismatches" not in output:
            accuracy = 1.0
        elif errors > 0:
            accuracy = 1.0 - (float(errors) / mismatches) if mismatches > 0 else 0.0
        
        # Calculate combined score (simple example - can be customized)
        combined_score = accuracy

        return {
            "accuracy": accuracy,
            "line_count": len(code.splitlines()),
            "combined_score": combined_score,
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
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "exec"], check=False)
        except:
            pass


if __name__ == '__main__':
    # Example usage (replace with your Verilog code)
    verilog_code = """
    module my_module (
        input clk,
        input rst,
        input [7:0] data_in,
        output reg [7:0] data_out
    );

    always @(posedge clk) begin
        if (rst) begin
            data_out <= 8'b0;
        end else begin
            data_out <= data_in + 1;
        end
    end

    endmodule
    """

    result = evaluate(verilog_code)
    print(result)