"""
Evaluator for Image Approximation Example.
Target: Heart Shape.
Metric: Intersection over Union (IoU) of the drawn circles vs the target shape.
"""

import numpy as np
import time
import sys
import os
import signal
import traceback

# --- Target Shape Definition ---
def is_inside_target_shape(x, y):
    """
    Heart shape formula: (x^2 + y^2 - 1)^3 - x^2 * y^3 <= 0
    Scaled and translated to fit in unit square [0,1]x[0,1]
    """
    # Transform [0,1] space to local heart space approx [-1.5, 1.5] x [-1.5, 1.5]
    # Center at (0.5, 0.5)
    
    # Shift center
    x_local = (x - 0.5) * 3.0
    y_local = (y - 0.5) * 3.0
    
    # Flip Y because often image coordinates run top-down, but math is bottom-up.
    # Actually standard Heart math usually has the pointy bit down.
    # (x^2 + y^2 - 1)^3 - x^2*y^3 = 0
    
    term1 = (x_local**2 + y_local**2 - 1) ** 3
    term2 = (x_local**2) * (y_local**3)
    
    return (term1 - term2) <= 0

# --- Evaluation Logic ---

def evaluate_iou(centers, radii, resolution=200):
    """
    Calculate IoU (Intersection over Union) by sampling points in the grid.
    """
    x = np.linspace(0, 1, resolution)
    y = np.linspace(0, 1, resolution)
    xv, yv = np.meshgrid(x, y)
    
    # Boolean mask for target shape (Ground Truth)
    target_mask = is_inside_target_shape(xv, yv)
    
    # Boolean mask for generated circles (Prediction)
    pred_mask = np.zeros_like(target_mask, dtype=bool)
    
    n_circles = len(radii)
    for i in range(n_circles):
        cx, cy = centers[i]
        r = radii[i]
        if r <= 0: continue
        
        # Distance map for this circle
        dist_sq = (xv - cx)**2 + (yv - cy)**2
        circle_mask = dist_sq <= r**2
        pred_mask = np.logical_or(pred_mask, circle_mask)
        
    # Calculate IoU
    intersection = np.logical_and(target_mask, pred_mask).sum()
    union = np.logical_or(target_mask, pred_mask).sum()
    
    if union == 0:
        return 0.0
        
    return float(intersection) / union

def run_evaluation(program_msg):
    """
    Evaluates the program.
    Expected to import/exec the program and get (centers, radii).
    """
    
    # Since this is running in the same process for simplicity in this example context,
    # or wrapped by OpenEvolve's runner. 
    # To match OpenEvolve standard pattern, we act as a library function 'evaluate(program_path)'
    pass # See 'evaluate' function below

def evaluate(program_path):
    """
    Main entry point called by OpenEvolve.
    """
    try:
        start_time = time.time()
        
        # Load the program dynamically
        directory = os.path.dirname(program_path)
        if directory not in sys.path:
            sys.path.insert(0, directory)
            
        spec = __import__('importlib.util').util.spec_from_file_location("program", program_path)
        program = __import__('importlib.util').util.module_from_spec(spec)
        spec.loader.exec_module(program)
        
        # Run the program
        centers, radii = program.run_approximation()
        
        centers = np.array(centers)
        radii = np.array(radii)
        
        # Sanity Checks
        if np.isnan(centers).any() or np.isnan(radii).any():
             return {
                "fitness": 0.0,
                "iou": 0.0,
                "valid": False,
                "error": "NaN values"
            }
            
        # Calc IoU
        iou = evaluate_iou(centers, radii)
        
        end_time = time.time()
        
        print(f"Evaluated IoU: {iou:.4f}")
        
        return {
            "fitness": iou, # Maximizing IoU
            "iou": iou,
            "combined_score": iou,
            "valid": True,
            "runtime": end_time - start_time
        }
        
    except Exception as e:
        traceback.print_exc()
        return {
            "fitness": 0.0,
            "iou": 0.0,
            "valid": False,
            "error": str(e)
        }

if __name__ == "__main__":
    # Test run
    # Mocking a path if run directly
    if len(sys.argv) > 1:
        print(evaluate(sys.argv[1]))
    else:
        print("Usage: python evaluator.py <path_to_program>")
