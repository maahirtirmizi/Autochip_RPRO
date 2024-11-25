// A heating/cooling thermostat controls both a heater (during winter) and an air conditioner (during summer). Generate a verilog code for it. 
// Requirements:
//
// 1. Operation Modes:
//    - Winter (mode input is high)
//    - Summer (mode input is low)
//
// 2. Control Logic:
//    - Winter Mode Operation:
//      * Monitor temperature using too_cold signal
//      * Control heating system appropriately
//      * No cooling needed
//    
//    - Summer Mode Operation:
//      * Monitor temperature using too_hot signal
//      * Control cooling system appropriately
//      * No heating needed
//
// 3. Fan Control:
//    - Should operate when heating or cooling is active
//    - Can be manually controlled by user
//
// 4. Additional Notes:
//    - Ensure proper control in both modes
//    - Consider temperature thresholds
//    - Handle manual overrides
//
module top_module(
    input mode,
    input too_cold, 
    input too_hot,
    input fan_on,
    output heater,
    output aircon,
    output fan
);
