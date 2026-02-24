module TopModule (
  input clk,
  input [7:0] d,
  input reset,
  output reg [7:0] q
);

  // Module body - leave empty or add minimal initialization
  initial begin
    q <= 8'b0; // Optional: Initialize q to a known state
  end

endmodule