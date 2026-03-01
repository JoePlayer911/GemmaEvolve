module TopModule (
  input in,
  input [9:0] state,
  output [9:0] next_state,
  output out1,
  output out2
);

  // Define state encoding (one-hot)
  localparam S0 = 10'b0000000001;
  localparam S1 = 10'b0000000010;
  localparam S2 = 10'b0000000100;
  localparam S3 = 10'b0000001000;
  localparam S4 = 10'b0000010000;
  localparam S5 = 10'b0000100000;
  localparam S6 = 10'b0001000000;
  localparam S7 = 10'b0010000000;
  localparam S8 = 10'b0100000000;
  localparam S9 = 10'b1000000000;

  // Define outputs for each state
  assign out1 = (state & S1) ? 1 : 0;
  assign out2 = (state & S3) ? 1 : 0;

  // Next state logic
  reg [9:0] next_state_reg;
  always @(*) begin
    next_state_reg = 0;

    case (state)
      S0: begin
        if (in)
          next_state_reg = S1;
        else
          next_state_reg = S0;
      end
      S1: begin
        if (in)
          next_state_reg = S2;
        else
          next_state_reg = S0;
      end
      S2: begin
        if (in)
          next_state_reg = S3;
        else
          next_state_reg = S0;
      end
      S3: begin
        if (in)
          next_state_reg = S4;
        else
          next_state_reg = S0;
      end
      S4: begin
        if (in)
          next_state_reg = S5;
        else
          next_state_reg = S0;
      end
      S5: begin
        if (in)
          next_state_reg = S6;
        else
          next_state_reg = S0;
      end
      S6: begin
        if (in)
          next_state_reg = S7;
        else
          next_state_reg = S0;
      end
      S7: begin
        if (in)
          next_state_reg = S8;
        else
          next_state_reg = S0;
      end
      S8: begin
        if (in)
          next_state_reg = S9;
        else
          next_state_reg = S0;
      end
      S9: begin
        if (in)
          next_state_reg = S0;
        else
          next_state_reg = S0;
      end
      default: next_state_reg = S0;
    endcase
  end

  assign next_state = next_state_reg;

endmodule