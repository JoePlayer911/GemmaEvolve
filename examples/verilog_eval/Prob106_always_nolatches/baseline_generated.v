module TopModule (
  input [15:0] scancode,
  output reg left,
  output reg down,
  output reg right,
  output reg up
);

  always @(scancode) begin
    if (scancode == 16'h06B) begin
      left <= 1;
      down <= 0;
      right <= 0;
      up <= 0;
    end else if (scancode == 16'h072) begin
      left <= 0;
      down <= 1;
      right <= 0;
      up <= 0;
    end else if (scancode == 16'h074) begin
      left <= 0;
      down <= 0;
      right <= 1;
      up <= 0;
    end else if (scancode == 16'h075) begin
      left <= 0;
      down <= 0;
      right <= 0;
      up <= 1;
    end else begin
      left <= 0;
      down <= 0;
      right <= 0;
      up <= 0;
    end
  end

endmodule