# OctoPrint-PrintLight

Control a printer light through a Raspberry Pi GPIO pin or a USB serial relay from OctoPrint. The plugin adds a
light-status indicator and toggle to the navbar, turns the light on when a print starts, and turns it off when a
print finishes, fails, or is cancelled.

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

Choose a controller in **Settings > Print Light**, configure it, and save. The light is initialized to off whenever
the plugin starts or its controller configuration changes.

### Raspberry Pi GPIO

1. Select **Raspberry Pi GPIO**.
2. Wire the light's control circuit to an available GPIO pin. Use an appropriate transistor, relay, or other
   interface circuit; do not connect a mains-powered light directly to a Raspberry Pi GPIO pin.
3. Enter the GPIO pin number. Pin numbers use Broadcom (BCM) numbering, not the physical header position. The
   default is BCM GPIO 1.
4. Enable **Invert** when the control circuit is active-low.

### USB serial relay

1. Select **USB serial relay**.
2. Connect the relay and identify its serial device, such as `/dev/ttyACM0`. For a stable device name on Linux,
   configure a udev rule that creates a symlink for the relay.
3. Enter that device path and the relay's baud rate. The included ATtiny85 firmware uses `9600`.
4. The relay must accept newline-delimited `ON` and `OFF` ASCII commands. See
   [`firmware/printlight_relay`](firmware/printlight_relay) for the included ATtiny85 implementation.

## Usage

- Click the lightbulb in the OctoPrint navbar to toggle the light manually. A filled bulb indicates that the light is
  on.
- PrintLight turns the light on for `PRINT_STARTED` and off for `PRINT_DONE`, `PRINT_FAILED`, and
  `PRINT_CANCELLED` events. A manual toggle remains in effect until the next relevant print event.

## API

The plugin exposes the standard OctoPrint plugin API endpoint at
`/api/plugin/printlight`. Use the usual OctoPrint API authentication and send a JSON `POST` body with one of these
commands:

| Command | Effect |
| --- | --- |
| `turnOn` | Turn the light on. |
| `turnOff` | Turn the light off. |
| `toggle` | Toggle the current light state. |
| `getState` | Return `{"isLightOn": true}` or `{"isLightOn": false}`. |

For example:

```bash
curl -X POST http://octopi.local/api/plugin/printlight \
  -H 'X-Api-Key: YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  --data '{"command":"turnOn"}'
```

## License

PrintLight is licensed under the [GNU Affero General Public License v3.0 or later](https://www.gnu.org/licenses/agpl-3.0.html).
