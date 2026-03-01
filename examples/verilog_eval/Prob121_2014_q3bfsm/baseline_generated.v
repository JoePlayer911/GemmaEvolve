module TopModule (
  input clk,
  input reset,
  input x,
  output reg z
);

  reg [2:0] y;

  always @(posedge clk) begin
    if (reset) begin
      y <= 3'b000;
    end else begin
      case (y)
        3'b000: begin
          if (x)
            y <= 3'b001;
          else
            y <= 3'b000;
        end
        3'b001: begin
          if (x)
            y <= 3'b010;
          else
            y <= 3'b000;
        end
        3'b010: begin
          if (x)
            y <= 3'b001;
          else
            y <= 3'b011;
        end
        3'b011: begin
          if (x)
            y <= 3'b000;
          else
            y <= 3'b011;
        end
        default: y <= 3'b000;
      endcase
    end
  end

  assign z = (y == 3'b001) ? 1 : 0;

endmodule