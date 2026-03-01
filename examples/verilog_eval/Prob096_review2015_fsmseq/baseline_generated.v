module TopModule (
  input clk,
  input reset,
  input data,
  output reg start_shifting
);

  // State definition
  typedef enum logic [1:0] {
    S0 = 2'b00,
    S1 = 2'b01,
    S2 = 2'b10,
    S3 = 2'b11,
    DETECTED = 2'b11
  } state_t;

  reg state, next_state;

  // State transition logic
  always_comb begin
    next_state = state;
    case (state)
      S0: begin
        if (data == 1'b1)
          next_state = S1;
        else
          next_state = S0;
      end
      S1: begin
        if (data == 1'b1)
          next_state = S2;
        else
          next_state = S0;
      end
      S2: begin
        if (data == 1'b0)
          next_state = S3;
        else
          next_state = S0;
      end
      S3: begin
        if (data == 1'b1)
          next_state = DETECTED;
        else
          next_state = S0;
      end
      DETECTED: next_state = DETECTED;
      default: next_state = S0;
    endcase
  end

  // State register
  always_ff @(posedge clk) begin
    if (reset)
      state <= S0;
    else
      state <= next_state;
  end

  // Output logic
  always_ff @(posedge clk) begin
    if (reset)
      start_shifting <= 1'b0;
    else if (state == DETECTED)
      start_shifting <= 1'b1;
    else if (state == S0 && start_shifting == 1'b1)
      start_shifting <= 1'b0;
    else
      start_shifting <= start_shifting;
  end
endmodule