# OctoPrint-PrintLight

Control a printer light through a Raspberry Pi GPIO pin from OctoPrint. The plugin adds a light-status indicator
and toggle to the navbar, turns the light on when a print starts, and turns it off when a print finishes, fails,
or is cancelled.

This project is adapted from the [PSU Control plugin](https://github.com/kantlivelong/OctoPrint-PSUControl).

## Compatibility

PrintLight supports Python 3.7 through 3.13 and requires hardware supported by
[`RPi.GPIO`](https://pypi.org/project/RPi.GPIO/), such as a Raspberry Pi. GPIO access is unavailable on typical
desktop OctoPrint installations.

## Installation

Install the plugin through OctoPrint's [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
using the following URL:

```text
https://github.com/tom0521/OctoPrint-PrintLight/archive/refs/heads/main.zip
```

## Configuration

1. Wire the light's control circuit to an available GPIO pin. Use an appropriate transistor, relay, or other
   interface circuit; do not connect a mains-powered light directly to a Raspberry Pi GPIO pin.
2. In **Settings > Print Light**, enter the GPIO pin number. Pin numbers use Broadcom (BCM) numbering, not the
   physical header position. The default is BCM GPIO 1.
3. Enable **Invert** when the control circuit is active-low.
4. Save the settings. The light is initialized to off when the plugin starts.

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
