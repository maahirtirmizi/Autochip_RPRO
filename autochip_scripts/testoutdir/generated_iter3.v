`timescale 1ns / 1ps
`define RESET_VAL 4'b0000

`timescale 1ns / 1ps

module top_module(
  input [2:0] vec, 
  output reg [2:0] outv,
  output reg o2,
  output reg o1,
  output reg o0
);

always @* begin
  outv = vec;
  o2 = vec[2];
  o1 = vec[1];
  o0 = vec[0];
end

endmodule