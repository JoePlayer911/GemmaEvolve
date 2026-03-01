module TopModule (
  input clock,
  input a,
  output reg p,
  output reg q
);

  always @(posedge clock) begin
    if (a == 1) begin
      p <= 1;
      q <= 1;
    end else if (a == 0) begin
      if (clock == 1) begin
        p <= 0;
        q <= 0;
      end
    end
  end

endmodule