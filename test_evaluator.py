
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from examples.verilog_optimization.evaluator import evaluate

def test():
    with open("examples/verilog_optimization/initial_program.v", "r") as f:
        code = f.read()
    
    print(f"Testing with code length: {len(code)}")
    print("--- Code Start ---")
    print(code)
    print("--- Code End ---")
    
    result = evaluate(code)
    print(f"Result: {result}")

if __name__ == "__main__":
    test()
