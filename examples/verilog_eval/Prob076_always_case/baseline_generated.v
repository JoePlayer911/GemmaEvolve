module TopModule (
  input [2:0] sel,
  input [3:0] data0,
  input [3:0] data1,
  input [3:0] data2,
  input [3:0] data3,
  input [3:0] data4,
  input [3:0] data5,
  output reg [3:0] out
);

  always @(*) begin
    if (sel == 0) begin
      out = data0;
    end else if (sel == 1) begin
      out = data1;
    end else if (sel == 2) begin
      out = data2;
    end else if (sel == 3) begin
      out = data3;
    end else if (sel == 4) begin
      out = data4;
    end else if (sel == 5) begin
      out = data5;
    end else begin
      out = 0;
    end
  end

endmodule