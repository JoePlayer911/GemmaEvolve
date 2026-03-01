module TopModule (
  input clk,
  input in,
  input reset,
  output out
);

  // Define state type
  typedef enum logic [1:0] {
    A,
    B,
    C,
    D
  } state_t;

  // Declare state variable
  state_t current_state, next_state;

  // State register
  always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
      current_state <= A;
    end else begin
      current_state <= next_state;
    end
  end

  // Next state logic
  always_comb begin
    next_state = current_state; // Default: stay in the same state

    case (current_state)
      A: begin
        if (in)
          next_state = B;
        else
          next_state = A;
      end
      B: begin
        if (in)
          next_state = C;
        else
          next_state = A;
      end
      C: begin
        if (in)
          next_state = D;
        else
          next_state = C;
      end
      D: begin
        if (in)
          next_state = A;
        else
          next_state = C;
      end
      default: begin
        next_state = A; // Should never happen, but good to have a default
      end
    endcase
  end

  // Output logic
  always_comb begin
    case (current_state)
      A: out = 1'b0;
      B: out = 1'b1;
      C: out = 1'b0;
      D: out = 1'b1;
      default: out = 1'bx; // Should never happen
    endcase
  end

endmodule