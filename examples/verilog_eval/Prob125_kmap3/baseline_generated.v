module TopModule (
  input a,
  input b,
  input c,
  input d,
  output reg out
);

  always @(*) begin
    if ((c == 0) && (a == 0)) begin
      out = 0;
    end else if ((c == 0) && (a == 1)) begin
      out = 0;
    end else begin
      out = 1;
    end
  end

endmodule