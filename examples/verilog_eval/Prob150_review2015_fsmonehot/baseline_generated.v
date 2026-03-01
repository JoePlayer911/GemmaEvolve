module TopModule (
  input d,
  input done_counting,
  input ack,
  input [9:0] state, // 10-bit one-hot current state
  output B3_next,
  output S_next,
  output S1_next,
  output Count_next,
  output Wait_next,
  output done,
  output counting,
  output shift_ena
);

  // Define state bits
  localparam S = 10'b1;
  localparam S1 = 10'b01;
  localparam S11 = 10'b001;
  localparam S110 = 10'b0001;
  localparam B0 = 10'b00001;
  localparam B1 = 10'b000001;
  localparam B2 = 10'b0000001;
  localparam B3 = 10'b00000001;
  localparam Count = 10'b000000001;
  localparam Wait = 10'b000000000;

  // Next state logic
  assign S_next = (state == S) ? (d ? S1 : S) : 0;
  assign S1_next = (state == S1) ? (d ? S11 : S1) : 0;
  assign S11_next = (state == S11) ? (d ? S110 : S11) : 0;
  assign S110_next = (state == S110) ? (d ? B0 : S110) : 0;
  assign B0_next = (state == B0) ? (ack ? B1 : B0) : 0;
  assign B1_next = (state == B1) ? (ack ? B2 : B1) : 0;
  assign B2_next = (state == B2) ? (ack ? B3 : B2) : 0;
  assign B3_next = (state == B3) ? (done_counting ? Count : B3) : 0;
  assign Count_next = (state == Count) ? (done_counting ? Wait : Count) : 0;
  assign Wait_next = (state == Wait) ? Wait : 0;

  // Combine next state signals into a single next_state signal
  wire [9:0] next_state;
  assign next_state = {S_next, S1_next, S11_next, S110_next, B0_next, B1_next, B2_next, B3_next, Count_next, Wait_next};

  // Output logic
  assign shift_ena = (state == B0) || (state == B1) || (state == B2) || (state == B3);
  assign counting = (state == Count);
  assign done = (state == Wait);

endmodule