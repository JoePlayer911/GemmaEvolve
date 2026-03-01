module TopModule (
  input clk,
  input reset,
  input [3:1] s,
  output reg fr3,
  output reg fr2,
  output reg fr1,
  output reg dfr
);

  // Define states
  localparam IDLE = 0;
  localparam RISING = 1;
  localparam FALLING = 2;

  reg state;
  reg [1:0] sensor_state;

  always @(posedge clk) begin
    if (reset) begin
      state <= IDLE;
      fr3 <= 1;
      fr2 <= 1;
      fr1 <= 1;
      dfr <= 1;
      sensor_state <= 0;
    end else begin
      case (state)
        IDLE: begin
          // Initial state - low water level, all valves open
          fr3 <= 1;
          fr2 <= 1;
          fr1 <= 1;
          dfr <= 1;

          // Detect sensor transitions to determine rising or falling
          if (s[1] == 1 && s[2] == 0) begin
            state <= RISING;
          end else if (s[1] == 0 && s[2] == 1) begin
            state <= FALLING;
          end
        end

        RISING: begin
          // Water level is rising
          if (s[1] == 1 && s[2] == 1) begin
            fr3 <= 1;
            fr2 <= 1;
            fr1 <= 0;
            dfr <= 1; //Supplemental valve open
          end else if (s[1] == 1 && s[2] == 0) begin
            fr3 <= 1;
            fr2 <= 1;
            fr1 <= 1;
            dfr <= 0;
          end else if (s[1] == 0 && s[2] == 1) begin
            fr3 <= 1;
            fr2 <= 0;
            fr1 <= 1;
            dfr <= 0;
          end else if (s[1] == 0 && s[2] == 0) begin
            fr3 <= 1;
            fr2 <= 1;
            fr1 <= 1;
            dfr <= 1;
            state <= IDLE;
          end
        end

        FALLING: begin
          // Water level is falling
          if (s[1] == 1 && s[2] == 1) begin
            fr3 <= 1;
            fr2 <= 1;
            fr1 <= 0;
            dfr <= 0; //Supplemental valve closed
          end else if (s[1] == 1 && s[2] == 0) begin
            fr3 <= 1;
            fr2 <= 1;
            fr1 <= 1;
            dfr <= 1;
          end else if (s[1] == 0 && s[2] == 1) begin
            fr3 <= 1;
            fr2 <= 0;
            fr1 <= 1;
            dfr <= 1;
          end else if (s[1] == 0 && s[2] == 0) begin
            fr3 <= 1;
            fr2 <= 1;
            fr1 <= 1;
            dfr <= 1;
            state <= IDLE;
          end
        end
      endcase
    end
  end

endmodule