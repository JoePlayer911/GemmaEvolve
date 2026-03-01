module TopModule (
  input clk,
  input j,
  input k,
  input areset,
  output out
);

  reg state;

  always @(posedge clk or posedge areset) begin
    if (areset) begin
      state <= 0; // OFF state
    end else begin
      if (state == 0) begin // OFF state
        if (j) begin
          state <= 1; // Transition to ON state
        end
      end else begin // ON state
        if (k) begin
          state <= 0; // Transition to OFF state
        end
      end
    end
  end

  assign out = state;

endmodule