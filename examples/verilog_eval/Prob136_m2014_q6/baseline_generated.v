module TopModule (
  input clk,
  input reset,
  input w,
  output z
);

  // Define the state type
  typedef enum logic [2:0] {
    A,
    B,
    C,
    D,
    E,
    F
  } state_t;

  // Declare the state variable
  state_t current_state, next_state;

  // Assign the output z (arbitrarily set to w for demonstration)
  assign z = w;

  // Sequential logic for state update
  always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
      current_state <= A;
    end else begin
      current_state <= next_state;
    end
  end

  // Combinational logic for next state and output
  always_comb begin
    next_state = current_state; // Default: stay in the current state

    case (current_state)
      A: begin
        if (w)
          next_state = B;
        else
          next_state = C;
      end
      B: begin
        next_state = D;
      end
      C: begin
        next_state = E;
      end
      D: begin
        next_state = F;
      end
      E: begin
        if (w)
          next_state = E; // Stay in E if w is 1
        else
          next_state = A;
      end
      F: begin
        if (!w)
          next_state = F; // Stay in F if w is 0
        else
          next_state = B;
      end
      default: begin
        next_state = A; // Default to state A in case of an invalid state
      end
    endcase
  end

endmodule