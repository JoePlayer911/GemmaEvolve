module TopModule (
  input clk,
  input load,
  input [255:0] data,
  output reg [255:0] q
);

  localparam GRID_SIZE = 16;
  localparam GRID_WIDTH = GRID_SIZE;
  localparam GRID_HEIGHT = GRID_SIZE;
  localparam GRID_SIZE_SQ = GRID_WIDTH * GRID_HEIGHT;

  reg [GRID_SIZE_SQ-1:0] current_grid;
  reg [GRID_SIZE_SQ-1:0] next_grid;

  integer i, j;

  always @(posedge clk) begin
    if (load) begin
      current_grid <= data;
    end else begin
      current_grid <= next_grid;
    end
  end

  always @(*) begin
    for (i = 0; i < GRID_WIDTH; i++) begin
      for (j = 0; j < GRID_HEIGHT; j++) begin
        integer index = i * GRID_HEIGHT + j;
        integer live_neighbors = 0;

        // Calculate neighbors, handling toroidal wrapping
        for (integer x = -1; x <= 1; x++) begin
          for (integer y = -1; y <= 1; y++) begin
            if (x == 0 && y == 0) continue; // Skip the cell itself

            integer neighbor_x = (i + x + GRID_WIDTH) % GRID_WIDTH;
            integer neighbor_y = (j + y + GRID_HEIGHT) % GRID_HEIGHT;
            integer neighbor_index = neighbor_x * GRID_HEIGHT + neighbor_y;

            live_neighbors = live_neighbors + current_grid[neighbor_index];
          end
        end

        // Apply Game of Life rules
        if (current_grid[index] == 1) begin // Alive cell
          if (live_neighbors == 2 || live_neighbors == 3) begin
            next_grid[index] = 1; // Stays alive
          end else begin
            next_grid[index] = 0; // Dies
          end
        } else begin // Dead cell
          if (live_neighbors == 3) begin
            next_grid[index] = 1; // Becomes alive
          end else begin
            next_grid[index] = 0; // Stays dead
          end
        end
      end
    end
  end

  assign q = current_grid;

endmodule