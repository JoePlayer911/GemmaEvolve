import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by simulating it against a reference model using Iverilog and VVP.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results:
        - accuracy: The accuracy of the module (float between 0.0 and 1.0).
        - line_count: The number of lines in the Verilog code.
        - combined_score: A combined score based on accuracy and line count (not implemented, set to accuracy for now).
        - error: An error message if any occurred during the evaluation (otherwise None).
    """
    try:
        exec_name = "a.out"
        candidate_file = "candidate.sv"
        testbench_file = "testbench.sv"
        ref_file = "ref.sv"

        with open(candidate_file, "w") as f:
            f.write(code)

        # Create a dummy reference module
        with open(ref_file, "w") as f:
            f.write("module ref (input clk, input enable, input [7:0] in, output reg [7:0] out);\n")
            f.write("  always @(posedge clk) begin\n")
            f.write("    if (enable) out = in;\n")
            f.write("    else out = 8'b0;\n")
            f.write("  end\n")
            f.write("endmodule\n")

        # Create a dummy testbench
        with open(testbench_file, "w") as f:
            f.write("module testbench;\n")
            f.write("  reg clk;\n")
            f.write("  reg enable;\n")
            f.write("  reg [7:0] in;\n")
            f.write("  wire [7:0] out;\n")
            f.write("  ref uut (clk, enable, in, out);\n")
            f.write("  initial begin\n")
            f.write("    clk = 0;\n")
            f.write("    enable = 1;\n")
            f.write("    in = 8'b123;\n")
            f.write("    #100 $finish;\n")
            f.write("  end\n")
            f.write("  always #5 clk = ~clk;\n")
            f.write("endmodule\n")

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", exec_name, candidate_file, testbench_file, ref_file],
            capture_output=True,
            text=True
        )

        if compile_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": len(code.splitlines()),
                "combined_score": 0.0,
                "error": f"Iverilog compilation failed: {compile_result.stderr}"
            }

        # Run the simulation
        simulation_result = subprocess.run(
            [exec_name],
            capture_output=True,
            text=True
        )

        output = simulation_result.stdout
        
        # Check for "FAIL"
        if "FAIL" in output:
            errors = re.findall(r"Mismatches: (\d+) in (\d+)", output)
            if errors:
                mismatches = int(errors[0][0])
                total_samples = int(errors[0][1])
                accuracy = 1.0 - (mismatches / total_samples)
                return {
                    "accuracy": accuracy,
                    "line_count": len(code.splitlines()),
                    "combined_score": accuracy,
                    "error": None
                }
            else:
                return {
                    "accuracy": 0.0,
                    "line_count": len(code.splitlines()),
                    "combined_score": 0.0,
                    "error": None
                }

        # Check for mismatches
        mismatches = re.findall(r"Mismatches: (\d+) in (\d+)", output)
        if mismatches:
            mismatches_count = int(mismatches[0][0])
            total_samples = int(mismatches[0][1])
            accuracy = 1.0 - (mismatches_count / total_samples)
            return {
                "accuracy": accuracy,
                "line_count": len(code.splitlines()),
                "combined_score": accuracy,
                "error": None
            }

        # Check for "PASS"
        if "PASS" in output:
            return {
                "accuracy": 1.0,
                "line_count": len(code.splitlines()),
                "combined_score": 1.0,
                "error": None
            }
        
        # No errors found
        return {
            "accuracy": 1.0,
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
        # Clean up the generated files
        import os
        try:
            os.remove(candidate_file)
            os.remove(testbench_file)
            os.remove(ref_file)
            os.remove(exec_name)
        except FileNotFoundError:
            pass