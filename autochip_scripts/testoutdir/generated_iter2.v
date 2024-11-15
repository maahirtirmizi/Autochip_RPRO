`timescale 1ns / 1ps
`define RESET_VAL 4'b0000

`timescale 1ns / 1ps

module top_module(
  input [2:0] vec, 
  output [2:0] outv,
  output o2,
  output o1,
  output o0
);

assign outv = vec;
assign o2 = vec[2];
assign o1 = vec[1];
assign o0 = vec[0];

endmodule