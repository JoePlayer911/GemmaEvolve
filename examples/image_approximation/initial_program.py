# EVOLVE-BLOCK-START
"""
Image Approximation via Circle Packing.
Goal: Arrange circles to approximate a hidden target shape (e.g., a Heart).
"""
import numpy as np

def construct_approximation():
    """
    Construct an arrangement of circles in a unit square.
    
    Returns:
        Tuple of (centers, radii)
        centers: np.array of shape (50, 2) with (x, y) coordinates
        radii: np.array of shape (50) with radius of each circle
    """
    n = 50 # Fixed number of circles
    centers = np.zeros((n, 2))
    radii = np.zeros(n)

    # Initial Strategy: Random Grid
    # Place circles in a grid and give them a small radius
    # Evolution should discover which ones to grow/move to match the shape
    
    grid_size = int(np.ceil(np.sqrt(n)))
    step = 1.0 / grid_size
    
    count = 0
    for i in range(grid_size):
        for j in range(grid_size):
            if count >= n:
                break
            
            # Center of the grid cell
            x = (i * step) + (step / 2)
            y = (j * step) + (step / 2)
            
            centers[count] = [x, y]
            radii[count] = step / 3.0 # Start small, non-overlapping
            
            count += 1
            
    return centers, radii

# EVOLVE-BLOCK-END

def run_approximation():
    """Wrapper to run the approximation constructor"""
    return construct_approximation()

def visualize(centers, radii):
    """
    Visualize the circle packing against the heart shape
    """
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
    import numpy as np

    fig, ax = plt.subplots(figsize=(8, 8))

    # Draw unit square
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.grid(True, linestyle=':', alpha=0.6)

    # Draw Heart Shape Contour for reference
    t = np.linspace(0, 2*np.pi, 1000)
    # Parametric heart equation for visualization (approximate)
    # (16sin^3 t, 13cos t - 5cos 2t - 2cos 3t - cos 4t)
    # Normalized to fit in [0,1]
    
    # Using the implicit equation from evaluator for accurate contour
    x = np.linspace(0, 1, 400)
    y = np.linspace(0, 1, 400)
    X, Y = np.meshgrid(x, y)
    # Heart function from evaluator: (x_loc^2 + y_loc^2 - 1)^3 - x_loc^2 * y_loc^3 <= 0
    # x_loc = (x - 0.5) * 3
    X_loc = (X - 0.5) * 3.0
    Y_loc = (Y - 0.5) * 3.0
    Z = (X_loc**2 + Y_loc**2 - 1)**3 - (X_loc**2) * (Y_loc**3)
    
    ax.contour(X, Y, Z, levels=[0], colors='red', linewidths=2, alpha=0.5)

    # Draw circles
    for i, (center, radius) in enumerate(zip(centers, radii)):
        if radius > 0:
            circle = Circle(center, radius, alpha=0.6, fc='blue', ec='black')
            ax.add_patch(circle)

    plt.title(f"Image Approximation (n={len(centers)})")
    plt.show()

if __name__ == "__main__":
    centers, radii = run_approximation()
    print(f"Generated {len(centers)} circles.")
    
    # Try to visualize if matplotlib is installed
    try:
        visualize(centers, radii)
    except ImportError:
        print("Install matplotlib to see visualization.")
