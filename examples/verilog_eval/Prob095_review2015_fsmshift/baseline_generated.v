module TopModule (
  input clk,
  input reset,
  output shift_ena
);

  reg [2:0] counter;
  reg shift_ena_reg;

  always @(posedge clk) begin
    if (reset) begin
      counter <= 0;
      shift_ena_reg <= 0;
    end else begin
      if (counter < 4) begin
        counter <= counter + 1;
        shift_ena_reg <= 1;
      end else begin
        counter <= 0;
        shift_ena_reg <= 0;
      end
    end
  end

  assign shift_ena = shift_ena_reg;

endmodule