module TopModule (
  input clk,
  input load,
  input [511:0] data,
  output reg [511:0] q
);

  // Module body - leave empty or add minimal initialization
  initial begin
    q <= 0; // Initialize q to zero (optional, but good practice)
  end

endmodule