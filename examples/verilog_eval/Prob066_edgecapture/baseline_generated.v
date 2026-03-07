module TopModule (
  input clk,
  input reset,
  input [31:0] in,
  output reg [31:0] out
);

  reg [31:0] prev_in;

  always @(posedge clk) begin
    if (reset) begin
      out <= 0;
      prev_in <= 0;
    end else begin
      out <= 0;
      for (integer i = 0; i < 32; i++) begin
        if (prev_in[i] == 1 && in[i] == 0) begin
          out[i] <= 1;
        end
      end
      prev_in <= in;
    end
  end

endmodule