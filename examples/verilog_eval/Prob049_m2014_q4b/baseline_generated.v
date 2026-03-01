module TopModule (
  input clk,
  input d,
  input ar,
  output logic q
);

  always_ff @(posedge clk, posedge ar) begin
    if (ar) begin
      q <= 0;
    end else begin
      q <= d;
    end
  end

endmodule