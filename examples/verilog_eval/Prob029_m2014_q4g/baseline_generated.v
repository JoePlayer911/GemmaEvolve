module TopModule (
  input in1,
  input in2,
  input in3,
  output logic out
);
  wire xnor_inter;
  assign xnor_inter = in1 ~^ in2;
  assign out = xnor_inter ^ in3;
endmodule