module TopModule (
  input [15:0] a,
  input [15:0] b,
  input [15:0] c,
  input [15:0] d,
  input [15:0] e,
  input [15:0] f,
  input [15:0] g,
  input [15:0] h,
  input [15:0] i,
  input [3:0] sel,
  output logic [15:0] out
);

  always_comb begin
    if (sel >= 4'b9) begin
      out = 16'hFFFF;
    end else begin
      case (sel)
        4'b0: out = a;
        4'b1: out = b;
        4'b2: out = c;
        4'b3: out = d;
        4'b4: out = e;
        4'b5: out = f;
        4'b6: out = g;
        4'b7: out = h;
        4'b8: out = i;
        default: out = 16'h0000; // Should not happen, but good practice
      endcase
    end
  end

endmodule