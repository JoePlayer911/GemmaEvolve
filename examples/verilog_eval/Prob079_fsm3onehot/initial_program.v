module TopModule (
  input in,
  input [3:0] state,
  output reg [3:0] next_state,
  output out
);

  // Default assignment to avoid latch issues.  Important!
  initial begin
    next_state = 0;
  end

endmodule