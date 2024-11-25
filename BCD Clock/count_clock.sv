// Design a 12-hour clock with BCD outputs. Implementation requirements:
//
// 1. CRITICAL: NO ARITHMETIC OPERATIONS ALLOWED
//    - ONLY use direct hex assignments with 8'h prefix
//    - CORRECT examples:
//      if (ss == 8'h09) ss <= 8'h10;
//      if (mm == 8'h59) mm <= 8'h00;
//    - INCORRECT examples (DO NOT USE):
//      ss <= ss + 1;        // NO! Never use addition
//      ss <= ss + 8'h01;    // NO! Never use addition
//      ss[3:0] <= ss[3:0] + 1;  // NO! Never manipulate bits
//
// 2. EXACT CONTROL STRUCTURE REQUIRED:
//    always @(posedge clk) begin        // ONLY use posedge clk
//        if (reset) begin               // Reset has highest priority
//            hh <= 8'h12;               // Must start at 12
//            mm <= 8'h00;               // Must start at 00
//            ss <= 8'h00;               // Must start at 00
//            pm <= 1'b0;                // Must start at AM
//        end
//        else if (ena) begin           // Only update when enabled
//            // Your clock logic here
//        end
//    end
//
// 3. EXACT SEQUENCE OF CHECKS REQUIRED:
//    if (hh == 8'h11 && mm == 8'h59 && ss == 8'h59) begin
//        hh <= 8'h12;
//        pm <= ~pm;        // ONLY toggle pm here
//    end
//    else if (hh == 8'h12 && mm == 8'h59 && ss == 8'h59)
//        hh <= 8'h01;
//
// 4. EXACT WRAPPING CONDITIONS:
//    - Seconds: if (ss == 8'h59) ss <= 8'h00;
//    - Minutes: if (ss == 8'h59 && mm == 8'h59) mm <= 8'h00;
//    - Hours: CHECK CONDITION ABOVE
//
// 5. IMPORTANT RULES:
//    - Each digit must stay between 0-9
//    - Only check minutes when seconds = 59
//    - Only check hours when minutes = 59 AND seconds = 59
//    - PM only toggles at 11:59:59 -> 12:00:00
//    - Each state must use exact hex values (8'h00 through 8'h59)
//    - Use separate checks for each digit transition
//
// 6. SEQUENCE EXAMPLES:
//    Seconds: 8'h00->8'h01->...->8'h58->8'h59->8'h00
//    Minutes: 8'h00->8'h01->...->8'h58->8'h59->8'h00
//    Hours: 8'h12->8'h01->...->8'h09->8'h10->8'h11->8'h12
//
// 7. FORBIDDEN PATTERNS:
//    - No arithmetic (+, -, *)
//    - No bit manipulation ([7:4] or [3:0])
//    - No decimal numbers (use 8'h__ only)
//    - No asynchronous reset
//
module top_module(
    input clk,
    input reset,
    input ena,
    output reg pm,
    output reg [7:0] hh,    // hours: [7:4] for tens digit, [3:0] for ones digit
    output reg [7:0] mm,    // minutes: [7:4] for tens digit, [3:0] for ones digit
    output reg [7:0] ss     // seconds: [7:4] for tens digit, [3:0] for ones digit
);
