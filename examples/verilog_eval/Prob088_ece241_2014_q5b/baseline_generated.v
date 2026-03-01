module TopModule (
  input clk,
  input areset,
  input x,
  output z
);

  // State definition using one-hot encoding
  localparam STATE_A = 2'b01;
  localparam STATE_B = 2'b10;

  // State variables
  reg [1:0] current_state;
  reg [1:0] next_state;

  // Output logic
  assign z = (current_state == STATE_B) ? x : ~x;

  // Sequential logic: State transition
  always @(posedge clk or posedge areset) begin
    if (areset) begin
      current_state <= STATE_A;
    end else begin
      current_state <= next_state;
    end
  end

  // Combinational logic: Next state logic
  always @(*) begin
    case (current_state)
      STATE_A: begin
        if (x == 1'b0)
          next_state = STATE_A;
        else
          next_state = STATE_B;
      end
      STATE_B: begin
        if (x == 1'b0)
          next_state = STATE_B;
        else
          next_state = STATE_B;
      end
      default:
        next_state = STATE_A; // Default state for safety
    endcase
  end

endmodule