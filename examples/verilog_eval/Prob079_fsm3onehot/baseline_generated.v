module TopModule (
  input in,
  input [3:0] state,
  output reg [3:0] next_state,
  output out
);

  reg [3:0] current_state;

  always @(*) begin
    current_state = state;

    case (current_state)
      4'b0000: begin // State A
        if (in == 0)
          next_state = 4'b0000;
        else
          next_state = 4'b0001;
      end
      4'b0001: begin // State B
        if (in == 0)
          next_state = 4'b0010;
        else
          next_state = 4'b0001;
      end
      4'b0010: begin // State C
        if (in == 0)
          next_state = 4'b0000;
        else
          next_state = 4'b0011;
      end
      4'b0011: begin // State D
        if (in == 0)
          next_state = 4'b0010;
        else
          next_state = 4'b0011;
      end
      default: next_state = 4'b0000;
    endcase

    out = (current_state == 4'b0011) ? 1 : 0;
  end

endmodule