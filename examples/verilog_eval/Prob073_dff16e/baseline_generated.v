module TopModule (
  input clk,
  input resetn,
  input [1:0] byteena,
  input [15:0] d,
  output reg [15:0] q
);

  reg [15:0] q_reg;

  always @(posedge clk or negedge resetn) begin
    if (!resetn) begin
      q_reg <= 16'b0;
    end else begin
      q_reg <= d;
    end
  end

  always @(*) begin
    q <= q_reg;
  end
endmodule