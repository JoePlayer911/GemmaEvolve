module TopModule (
  input clk,
  input x,
  input [2:0] y,
  output reg Y0,
  output reg z
);

  reg [2:0] next_y;

  always @(posedge clk) begin
    Y0 <= ~Y0;
    next_y <= next_state_logic(y, x);
  end

  assign z = output_logic(y, x);

  function [2:0] next_state_logic (input [2:0] current_y, input x);
    case (current_y)
      3'b000: begin
        if (x == 1'b0)
          next_state_logic = 3'b001;
        else
          next_state_logic = 3'b000;
      end
      3'b001: begin
        if (x == 1'b0)
          next_state_logic = 3'b010;
        else
          next_state_logic = 3'b000;
      end
      3'b010: begin
        if (x == 1'b0)
          next_state_logic = 3'b001;
        else
          next_state_logic = 3'b011;
      end
      3'b011: begin
        if (x == 1'b0)
          next_state_logic = 3'b010;
        else
          next_state_logic = 3'b000;
      end
      default: next_state_logic = 3'b000;
    endcase
  endfunction

  function reg output_logic (input [2:0] current_y, input x);
    case (current_y)
      3'b000: begin
        output_logic = 1'b0;
      end
      3'b001: begin
        output_logic = 1'b1;
      end
      3'b010: begin
        output_logic = 1'b0;
      end
      3'b011: begin
        output_logic = 1'b1;
      end
      default: output_logic = 1'b0;
    endcase
  endfunction

endmodule