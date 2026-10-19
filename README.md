# OctoPrint-PrintLight

Control a printer light and PSU through independent Raspberry Pi GPIO pins or USB serial relays from OctoPrint. The
plugin adds light and PSU status toggles to the navbar, turns the light on when a print starts, and turns it off when
a print finishes, fails, or is cancelled.

This project is adapted from the [PSU Control plugin](https://github.com/kantlivelong/OctoPrint-PSUControl).

## Compatibility

PrintLight supports Python 3.7 through 3.13. GPIO control requires a system with
[`RPi.GPIO`](https://pypi.org/project/RPi.GPIO/), such as a Raspberry Pi. USB serial control works on any system
where the relay exposes a serial device. The plugin installs its USB serial dependency automatically; install
`RPi.GPIO` separately when using GPIO on a system where it is not already available.

## Installation

Install the plugin through OctoPrint's [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
using the following URL:

```text
https://github.com/tom0521/OctoPrint-PrintLight/archive/refs/heads/main.zip
```

## Configuration

Choose a controller for both **Light** and **PSU** in **Settings > Print Light**, configure them, and save. Each
output is initialized to off whenever the plugin starts or its controller configuration changes. Configure separate
GPIO pins, or use the same USB serial device and baud rate for both outputs.

Enable **Auto-connect printer** in the PSU settings to have OctoPrint connect after the PSU turns on. Set
**Connection delay** to allow enough time for the printer and its USB serial interface to boot; the default is
10 seconds. Turning the PSU off, changing settings, or shutting down OctoPrint cancels any pending connection.

### Raspberry Pi GPIO

1. Select **Raspberry Pi GPIO**.
2. Wire each output's control circuit to a separate available GPIO pin. Use an appropriate transistor, relay, or other
   interface circuit; do not connect a mains-powered light directly to a Raspberry Pi GPIO pin.
3. Enter the GPIO pin number for each output. Pin numbers use Broadcom (BCM) numbering, not the physical header
   position. The defaults are BCM GPIO 1 for Light and BCM GPIO 2 for PSU.
4. Enable **Invert** for each output when its control circuit is active-low.

### USB serial relay

1. Select **USB serial relay**.
2. Connect the relay and identify its serial device, such as `/dev/ttyACM0`. To control both outputs with the
   included dual-relay ATtiny85 firmware, select **USB serial relay** for both Light and PSU and enter the same
   device path and baud rate. The plugin opens one shared serial connection.
   For a stable device name on Linux, configure a udev rule that creates a symlink for the relay.
3. Enter that device path and the relay's baud rate. The included ATtiny85 firmware uses `9600`.
4. The relay must accept newline-delimited `LIGHT ON`, `LIGHT OFF`, `PSU ON`, and `PSU OFF` ASCII commands. See
   [`firmware/printlight_relay`](firmware/printlight_relay) for the included ATtiny85 implementation and wiring.

## Usage

- Click the lightbulb in the OctoPrint navbar to toggle the light manually. A filled bulb indicates that the light is
  on.
- Click the power icon in the OctoPrint navbar to toggle the PSU manually. A gray icon indicates that the PSU is off.
- When PSU auto-connect is enabled, turning on the PSU schedules an OctoPrint printer connection after the configured
  delay.
- PrintLight turns the light on for `PRINT_STARTED` and off for `PRINT_DONE`, `PRINT_FAILED`, and
  `PRINT_CANCELLED` events. PSU state is only changed manually. A manual light toggle remains in effect until the next
  relevant print event.

## API

The plugin exposes the standard OctoPrint plugin API endpoint at
`/api/plugin/printlight`. Use the usual OctoPrint API authentication and send a JSON `POST` body with one of these
commands:

| Command | Effect |
| --- | --- |
| `turnOn` | Turn the light on. |
| `turnOff` | Turn the light off. |
| `toggle` | Toggle the current light state. |
| `psuTurnOn` | Turn the PSU on. |
| `psuTurnOff` | Turn the PSU off. |
| `psuToggle` | Toggle the PSU. |
| `getState` | Return `{"isLightOn": true, "isPsuOn": false}`. |

For example:

```bash
curl -X POST http://octopi.local/api/plugin/printlight \
  -H 'X-Api-Key: YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  --data '{"command":"turnOn"}'
```

## License

PrintLight is licensed under the [GNU Affero General Public License v3.0 or later](https://www.gnu.org/licenses/agpl-3.0.html).
