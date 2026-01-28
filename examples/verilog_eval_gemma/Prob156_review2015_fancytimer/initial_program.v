module TopModule (
  input wire clk,
  input wire reset,
  input wire data,
  output wire [3:0] count,
  output reg counting,
  output reg done,
  input wire ack
);

  // Default assignments (important for synthesis)
  initial begin
    counting = 0;
    done = 0;
    count = 0;
  end


endmodule