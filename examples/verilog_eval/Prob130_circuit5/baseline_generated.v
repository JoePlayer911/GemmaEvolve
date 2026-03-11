module TopModule (
  input [3:0] a,
  input [3:0] b,
  input [3:0] c,
  input [3:0] d,
  input [3:0] e,
  output reg [3:0] q
);

  always @(*) begin
    if (c >= 10) begin
      q = 4'b1111; // f
    end else if (c == a) begin
      q = a;
    end else if (c == b) begin
      q = b;
    end else if (c == c) begin
      q = c;
    end else if (c == d) begin
      q = d;
    end else if (c == e) begin
      q = e;
    end else begin
      q = c;
    end
  end

endmodule