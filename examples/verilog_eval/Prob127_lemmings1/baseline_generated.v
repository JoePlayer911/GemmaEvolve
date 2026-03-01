module TopModule (
  input clk,
  input areset,
  input bump_left,
  input bump_right,
  output walk_left,
  output walk_right
);

  reg state;

  always @(posedge clk or posedge areset) begin
    if (areset) begin
      state <= 0; // Initial state: walk_left
    end else begin
      if (bump_left || bump_right || (bump_left && bump_right)) begin
        state <= 1; // Switch direction
      end
    end
  end

  assign walk_left = (state == 0);
  assign walk_right = (state == 1);

endmodule