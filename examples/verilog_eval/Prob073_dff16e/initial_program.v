module TopModule (
  input clk,
  input resetn,
  input [1:0] byteena,
  input [15:0] d,
  output reg [15:0] q
);

  // Module body - leave empty or add minimal initialization
  initial begin
    q <= 0; // Optional: Initialize q to a known state
  end

endmodule