# Image Approximation Example

This example challenges OpenEvolve to "draw" a shape using a set of 50 circles.
The target shape is a Heart.

## The Challenge

- **Objective**: Maximize Intersection over Union (IoU) with a mathematical Heart shape.
- **Constraints**: 
    - 50 circles maximum.
    - Canvas: Unit square [0, 1] x [0, 1].
    - Heart center: (0.5, 0.5).

## How it works

The `evaluator.py` defines the heart shape using an inequality function:
`((x-0.5)*3)^2 + ((y-0.5)*3)^2 - 1)^3 - ((x-0.5)*3)^2 * ((y-0.5)*3)^3 <= 0`

OpenEvolve modifies `initial_program.py` to change the `construct_approximation` function. It tries to find the best arrangement of circles to cover the heart mask without spilling over.

## Running the Example

```bash
# Run the evolution
python openevolve-run.py examples/image_approximation/initial_program.py \
  examples/image_approximation/evaluator.py \
  --config examples/image_approximation/config.yaml \
  --iterations 50
```

## Visualization

To check the score of the initial program:
```bash
python examples/image_approximation/evaluator.py examples/image_approximation/initial_program.py
```
