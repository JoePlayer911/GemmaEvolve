module TopModule (
  input clk,
  input [7:0] d,
  input areset,
  output reg [7:0] q
);

  // Module body - leave empty or add minimal initialization
  initial begin
    q <= 8'b0; // Optional initialization
  end

endmodule