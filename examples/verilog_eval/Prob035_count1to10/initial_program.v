module TopModule (
  input clk,
  input reset,
  output reg [3:0] q
);

  // Optional: Add comments to describe the module's purpose here.
  // For example:
  // This module implements a simple counter.

  // Optional: Declare any internal signals here.
  // Example:
  // reg [3:0] internal_counter;

  // Optional: Always block for sequential logic.  This is *required*
  // since 'q' is declared as 'reg'.
  always @(posedge clk or posedge reset) begin
    if (reset) begin
      q <= 4'b0000; // Initial value on reset
    end else begin
      // Logic goes here.  Placeholder.
      q <= q; // Keeps the value, preventing latching
    end
  end

endmodule