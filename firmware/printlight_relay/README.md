# ATtiny85 USB Serial Relay Firmware

This sketch targets an ATtiny85 board with the Digispark/DigiCDC USB stack. It exposes a USB serial device and
accepts newline-delimited ASCII commands:

```text
ON
OFF
```

## Uploading

1. In the Arduino IDE, install and select a Digispark ATtiny85 board package that provides the `DigiCDC` library.
2. Open `printlight_relay.ino`, select the appropriate Digispark ATtiny85 board, and upload it.
3. Wire the relay input to physical pin `P1` (ATtiny85 PB1). Set `RELAY_ACTIVE_LOW` to `true` when the relay is
   active-low.
4. Connect the board to the OctoPrint host and configure the resulting serial path in PrintLight.

The relay is explicitly set to off in `setup()` before USB serial control begins. Do not drive a relay coil directly
from the ATtiny85 pin; use a suitable driver circuit or relay module.
