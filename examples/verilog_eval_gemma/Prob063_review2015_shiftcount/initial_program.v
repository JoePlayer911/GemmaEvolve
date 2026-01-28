module TopModule (
  input clk,
  input shift_ena,
  input count_ena,
  input data,
  output reg [3:0] q
);

  // Module body - leave empty or add minimal initialization
  initial begin
    q <= 4'b0000; // Optional: Initialize q
  end

endmodule