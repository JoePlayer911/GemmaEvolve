module TopModule (
  input clk,
  input [7:0] in,
  output reg [7:0] pedge
);

  reg [7:0] prev_in;

  always @(posedge clk) begin
    pedge <= in;
  end

  always @(posedge clk) begin
    prev_in <= in;
  end

  always @(posedge clk) begin
    if (in != prev_in) begin
      if (prev_in == 0 && in == 1) begin
        pedge <= 1'b1;
      end else begin
        pedge <= 1'b0;
      end
    end else begin
      pedge <= 1'b0;
    end
  end
endmodule