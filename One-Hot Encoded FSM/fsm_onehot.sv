// Given state machine: 1 input, 2 outputs (out1,out2)
// CRITICAL: Next state equations for FSM
// 1. next_state[0]: Goes to S0 when:
//    - in=0 AND current state is S1-S4,S7-S9
//    - in=0 AND state[0]=1 (stay in S0)
//
// 2. next_state[1]: Goes to S1 when:
//    - in=1 AND state[0]=1
//    - in=1 AND state[8]=1
//    - in=1 AND state[9]=1
//
// 3. next_state[2-6]: Simple transitions
//    - next_state[2] = in & state[1]
//    - next_state[3] = in & state[2]
//    - next_state[4] = in & state[3]
//    - next_state[5] = in & state[4]
//    - next_state[6] = in & state[5]
//
// 4. next_state[7]: Special case
//    - Goes high when in=1 AND (state[6]=1 OR state[7]=1)
//
// 5. next_state[8]: Goes to S8 when
//    - in=0 AND state[5]=1
//
// 6. next_state[9]: Goes to S9 when
//    - in=0 AND state[6]=1
//
// OUTPUTS:
// out1 = state[8] | state[9]
// out2 = state[7] | state[9]

module top_module (
    input in,
    input [9:0] state,
    output [9:0] next_state,
    output out1,
    output out2);
