module TopModule (
  input clk,
  input x,
  input [2:0] y,
  output reg Y0,
  output reg z
);

  // Module body - leave empty or add minimal initialization
  initial begin
    Y0 <= 0;
    z <= 0;
  end

endmodule