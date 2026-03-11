module TopModule (
  input clk,
  input in,
  input reset,
  output reg done
);

  // State definition
  typedef enum logic [2:0] {
    IDLE,
    START_RECEIVED,
    RECEIVING_DATA,
    STOP_RECEIVED
  } state_t;

  reg state, next_state;

  // Internal registers
  reg [7:0] received_data;
  reg [2:0] bit_count;

  // Assign done signal
  assign done = (state == IDLE && bit_count == 0);

  // State transition logic
  always_ff @(posedge clk or posedge reset) begin
    if (reset) begin
      state <= IDLE;
      bit_count <= 0;
      received_data <= 0;
      done <= 0;
    end else begin
      state <= next_state;
      if (state == RECEIVING_DATA) begin
        received_data <= {received_data[6:0], in};
        bit_count <= bit_count + 1;
      end
    end
  end

  // Next state logic
  always_comb begin
    next_state = state;
    case (state)
      IDLE: begin
        if (in == 0) begin
          next_state = START_RECEIVED;
          bit_count = 0;
        end else begin
          next_state = IDLE;
        end
      end
      START_RECEIVED: begin
        next_state = RECEIVING_DATA;
        bit_count = 0;
      end
      RECEIVING_DATA: begin
        if (bit_count == 8) begin
          next_state = STOP_RECEIVED;
        end else begin
          next_state = RECEIVING_DATA;
        end
      end
      STOP_RECEIVED: begin
        if (in == 1) begin
          next_state = IDLE;
          done = 1;
          bit_count = 0;
        end else begin
          next_state = STOP_RECEIVED;
        end
      end
      default: begin
        next_state = IDLE;
        done = 0;
        bit_count = 0;
      end
    endcase
  end
endmodule