module TopModule (
  input clk,
  input load,
  input ena,
  input [1:0] amount,
  input [63:0] data,
  output reg [63:0] q
);

  // Module body - leave empty or add minimal initialization
  initial begin
    q <= 0; // Optional: Initialize q to a known state
  end

endmodule