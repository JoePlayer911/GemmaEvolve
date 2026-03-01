module TopModule (
  input clk,
  input aresetn,
  input x,
  output reg z
);

  // Define states
  typedef enum logic [1:0] {
    S0,
    S1,
    S2,
    S3
  } state_t;

  reg state_t current_state, next_state;

  // State register update (synchronous)
  always @(posedge clk or negedge aresetn) begin
    if (!aresetn) begin
      current_state <= S0;
    end else begin
      current_state <= next_state;
    end
  end

  // Next state logic
  always_comb begin
    next_state = current_state; // Default: stay in the same state
    case (current_state)
      S0: begin
        if (x)
          next_state = S1;
        else
          next_state = S0;
      end
      S1: begin
        if (!x)
          next_state = S2;
        else
          next_state = S1;
      end
      S2: begin
        if (x)
          next_state = S3;
        else
          next_state = S0;
      end
      S3: begin
        if (x)
          next_state = S1; // Allow overlapping sequences
        else
          next_state = S0;
      end
      default: next_state = S0; // Should not happen, but good to have
    endcase
  end

  // Output logic
  always_comb begin
    z = 0; // Default: z is 0
    case (current_state)
      S3: z = 1;
      default: z = 0;
    endcase
  end

endmodule