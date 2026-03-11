module TopModule (
  input clk,
  input reset,
  input ena,
  output reg pm,
  output reg [7:0] hh,
  output reg [7:0] mm,
  output reg [7:0] ss
);

  reg [3:0] hour_bcd;
  reg [3:0] minute_bcd;
  reg [3:0] second_bcd;

  always @(posedge clk) begin
    if (reset) begin
      hour_bcd <= 4'b1011; // 12 in BCD
      minute_bcd <= 4'b0000; // 00 in BCD
      second_bcd <= 4'b0000; // 00 in BCD
      pm <= 0; // AM
    end else if (ena) begin
      if (second_bcd == 4'b1111) begin
        second_bcd <= 4'b0000;
        if (minute_bcd == 4'b1111) begin
          minute_bcd <= 4'b0000;
          if (hour_bcd == 4'b1100) begin // 12 in BCD
            hour_bcd <= 4'b0001; // 1 in BCD
            pm <= 1; // PM
          end else if (hour_bcd == 4'b1010) begin //10 in BCD
            hour_bcd <= 4'b0011; // 11 in BCD
          end else begin
            hour_bcd <= hour_bcd + 4'b0001; // Increment hour
          end
        end else begin
          minute_bcd <= minute_bcd + 4'b0001; // Increment minute
        end
      end else begin
        second_bcd <= second_bcd + 4'b0001; // Increment second
      end
    end
  end

  assign hh = hour_bcd;
  assign mm = minute_bcd;
  assign ss = second_bcd;

endmodule