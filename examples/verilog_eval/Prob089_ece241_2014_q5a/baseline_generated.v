module TopModule (
  input clk,
  input areset,
  input x,
  output reg z
);

  // Define the states of the Moore machine
  typedef enum logic [1:0] {
    IDLE,
    CALC_0,
    CALC_1
  } state_t;

  reg state, next_state;

  // State transition logic
  always_comb begin
    case (state)
      IDLE: begin
        if (areset) begin
          next_state = IDLE;
        end else begin
          next_state = CALC_0;
        end
      end
      CALC_0: begin
        if (areset) begin
          next_state = IDLE;
        end else begin
          next_state = CALC_1;
        end
      end
      CALC_1: begin
        if (areset) begin
          next_state = IDLE;
        end else begin
          next_state = IDLE;
        end
      end
      default: next_state = IDLE;
    endcase
  end

  // State update logic
  always_ff @(posedge clk) begin
    if (areset) begin
      state <= IDLE;
    end else begin
      state <= next_state;
    end
  end

  // Output logic
  always_comb begin
    case (state)
      IDLE: z = 0;
      CALC_0: z = ~x;
      CALC_1: z = ~x;
      default: z = 0;
    endcase
  end

endmodule