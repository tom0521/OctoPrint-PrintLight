# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import octoprint.printer

import threading

from flask import jsonify
from octoprint.events import Events

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

try:
    import serial
except ImportError:
    serial = None


class RelayController(object):

    def __init__(self, plugin, name, settings_prefix):
        self._plugin = plugin
        self._name = name
        self._settings_prefix = settings_prefix
        self.controller = None
        self.gpio_pin = None
        self.gpio_invert = False
        self.serial_connection = None
        self._serial_connection_key = None
        self.gpio_initialized = False
        self.is_on = False

    def configure(self):
        self.shutdown()
        self.controller = None
        self.is_on = False

        controller = self._settings_value("controller")
        self.gpio_pin = self._settings_value("gpio", integer=True)
        self.gpio_invert = self._settings_value("gpioInvert", boolean=True)
        serial_port = self._settings_value("serialPort")
        serial_baudrate = self._settings_value("serialBaudrate", integer=True)

        if controller == "gpio":
            if GPIO is None:
                self._plugin._logger.error(
                    "%s GPIO control is selected, but RPi.GPIO is not installed",
                    self._name,
                )
                return

            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.gpio_pin, GPIO.OUT)
            except (RuntimeError, ValueError) as error:
                self._plugin._logger.error(
                    "Could not initialize %s GPIO pin %s: %s",
                    self._name.lower(),
                    self.gpio_pin,
                    error,
                )
                return

            self.gpio_initialized = True
            self.controller = controller
        elif controller == "usb_serial":
            if serial is None:
                self._plugin._logger.error(
                    "%s USB serial control is selected, but pyserial is not installed",
                    self._name,
                )
                return

            try:
                (
                    self.serial_connection,
                    self._serial_connection_key,
                ) = self._plugin.acquire_serial_connection(
                    serial_port, serial_baudrate
                )
            except (serial.SerialException, OSError, ValueError) as error:
                self._plugin._logger.error(
                    "Could not open %s USB relay on %s: %s",
                    self._name.lower(),
                    serial_port,
                    error,
                )
                return

            self.controller = controller
        else:
            self._plugin._logger.error(
                "Unsupported %s controller: %s", self._name.lower(), controller
            )
            return

        self.set_state(False)

    def set_state(self, state):
        if self.controller == "gpio":
            try:
                GPIO.output(self.gpio_pin, state ^ self.gpio_invert)
            except (RuntimeError, ValueError) as error:
                self._plugin._logger.error(
                    "Could not set %s GPIO state: %s", self._name.lower(), error
                )
                return False
        elif self.controller == "usb_serial":
            try:
                command = "{} {}\n".format(
                    self._name.upper(), "ON" if state else "OFF"
                ).encode("ascii")
                self.serial_connection.write(command)
                self.serial_connection.flush()
            except (serial.SerialException, OSError, ValueError) as error:
                self._plugin._logger.error(
                    "Could not set %s USB relay state: %s", self._name.lower(), error
                )
                return False
        else:
            self._plugin._logger.error(
                "Cannot set %s state because no controller is available",
                self._name.lower(),
            )
            return False

        self.is_on = state
        return True

    def shutdown(self):
        if self.serial_connection is not None:
            self._plugin.release_serial_connection(self._serial_connection_key)
            self.serial_connection = None
            self._serial_connection_key = None

        if self.gpio_initialized:
            GPIO.cleanup(self.gpio_pin)
            self.gpio_initialized = False

    def _settings_value(self, name, integer=False, boolean=False):
        key = [self._settings_prefix + name]
        if integer:
            return self._plugin._settings.get_int(key)
        if boolean:
            return self._plugin._settings.get_boolean(key)
        return self._plugin._settings.get(key)


class PrintLightPlugin(octoprint.plugin.AssetPlugin,
                       octoprint.plugin.EventHandlerPlugin,
                       octoprint.plugin.SettingsPlugin,
                       octoprint.plugin.ShutdownPlugin,
                       octoprint.plugin.SimpleApiPlugin,
                       octoprint.plugin.TemplatePlugin):

    def __init__(self):
        self.light_controller = RelayController(self, "Light", "")
        self.psu_controller = RelayController(self, "PSU", "psu")
        self._psu_connect_timer = None
        self._psu_connect_timer_lock = threading.Lock()
        self._psu_connect_generation = 0
        self._serial_connections = {}
        self._serial_connections_lock = threading.Lock()

    ##~~ Light and PSU Control Functions

    def turn_on(self):
        self._logger.debug("Turning print light on")
        self._set_light_state(True)

    def turn_off(self):
        self._logger.debug("Turning print light off")
        self._set_light_state(False)

    def toggle(self):
        self._logger.debug("Toggling light")
        self._set_light_state(not self.light_controller.is_on)

    def turn_psu_on(self):
        self._logger.debug("Turning PSU on")
        if self._set_psu_state(True):
            self._schedule_printer_connect()

    def turn_psu_off(self):
        self._logger.debug("Turning PSU off")
        self._cancel_printer_connect()
        self._set_psu_state(False)

    def toggle_psu(self):
        self._logger.debug("Toggling PSU")
        if self.psu_controller.is_on:
            self.turn_psu_off()
        else:
            self.turn_psu_on()

    def _set_light_state(self, state):
        if self.light_controller.set_state(state):
            self._send_state_message()

    def _set_psu_state(self, state):
        if self.psu_controller.set_state(state):
            self._send_state_message()
            return True
        return False

    def _schedule_printer_connect(self):
        if not self._settings.get_boolean(["psuAutoConnect"]):
            return

        delay = self._settings.get_float(["psuAutoConnectDelay"])
        self._cancel_printer_connect()
        with self._psu_connect_timer_lock:
            generation = self._psu_connect_generation
            timer = threading.Timer(
                delay,
                self._connect_printer_after_psu_start,
                args=[generation],
            )
            timer.daemon = True
            self._psu_connect_timer = timer
        timer.start()
        self._logger.debug("Scheduling printer connection %s seconds after PSU turn-on", delay)

    def _connect_printer_after_psu_start(self, generation):
        with self._psu_connect_timer_lock:
            if generation != self._psu_connect_generation:
                return
            self._psu_connect_timer = None

        if not self.psu_controller.is_on:
            return

        try:
            self._printer.connect()
        except (OSError, ValueError) as error:
            self._logger.error("Could not connect to the printer after PSU turn-on: %s", error)

    def _cancel_printer_connect(self):
        with self._psu_connect_timer_lock:
            self._psu_connect_generation += 1
            if self._psu_connect_timer is not None:
                self._psu_connect_timer.cancel()
                self._psu_connect_timer = None

    def _send_state_message(self):
        self._plugin_manager.send_plugin_message(
            self._identifier,
            dict(
                isLightOn=self.light_controller.is_on,
                isPsuOn=self.psu_controller.is_on,
            ),
        )

    def acquire_serial_connection(self, port, baudrate):
        key = (port, baudrate)
        with self._serial_connections_lock:
            connection_data = self._serial_connections.get(key)
            if connection_data is None:
                connection_data = dict(
                    connection=serial.Serial(
                        port=port,
                        baudrate=baudrate,
                        timeout=1,
                        write_timeout=1,
                    ),
                    users=0,
                )
                self._serial_connections[key] = connection_data

            connection_data["users"] += 1
            return connection_data["connection"], key

    def release_serial_connection(self, key):
        with self._serial_connections_lock:
            connection_data = self._serial_connections.get(key)
            if connection_data is None:
                return

            connection_data["users"] -= 1
            if connection_data["users"] == 0:
                connection_data["connection"].close()
                del self._serial_connections[key]

    ##~~ AssetPlugin

    def get_assets(self):
        return dict(
            js=["js/printlight.js"],
            css=["css/printlight.min.css"]
        )

    ##~~ EventHandlerPlugin mixin

    def on_event(self, event, payload):
        if event == Events.PRINT_STARTED:
            self._logger.debug("Print started")
            self.turn_on()
        elif event in [Events.PRINT_DONE, Events.PRINT_FAILED, Events.PRINT_CANCELLED]:
            self._logger.debug("Print ended")
            self.turn_off()
        elif event == Events.CLIENT_OPENED:
            self._send_state_message()

    ##~~ SettingsPlugin mixin

    def on_settings_initialized(self):
        self._configure_controllers()

    def on_settings_save(self, data):
        super(PrintLightPlugin, self).on_settings_save(data)
        self._configure_controllers()

    def _configure_controllers(self):
        self._cancel_printer_connect()
        self.light_controller.configure()
        self.psu_controller.configure()
        self._send_state_message()

    def get_settings_defaults(self):
        return dict(
            controller="gpio",
            gpio=1,
            gpioInvert=False,
            serialPort="/dev/ttyACM0",
            serialBaudrate=9600,
            psuController="gpio",
            psuGpio=2,
            psuGpioInvert=False,
            psuSerialPort="/dev/ttyACM1",
            psuSerialBaudrate=9600,
            psuAutoConnect=False,
            psuAutoConnectDelay=10,
        )

    ##~~ ShutdownPlugin mixin

    def on_shutdown(self):
        self._cancel_printer_connect()
        self.light_controller.shutdown()
        self.psu_controller.shutdown()

    ##~~ TemplatePlugin mixin

    def get_template_configs(self):
        return [
            dict(type="navbar", custom_bindings=True),
            dict(type="settings", custom_bindings=False)
        ]

    ##~~ SimpleApiPlugin mixin

    def get_api_commands(self):
        return dict(
            turnOn=[],
            turnOff=[],
            toggle=[],
            psuTurnOn=[],
            psuTurnOff=[],
            psuToggle=[],
            getState=[],
        )

    def on_api_get(self, request):
        return self.on_api_command("getState", [])

    def on_api_command(self, command, data):
        self._logger.debug("API call: %s", command)
        if command == "turnOn":
            self.turn_on()
        elif command == "turnOff":
            self.turn_off()
        elif command == "toggle":
            self.toggle()
        elif command == "psuTurnOn":
            self.turn_psu_on()
        elif command == "psuTurnOff":
            self.turn_psu_off()
        elif command == "psuToggle":
            self.toggle_psu()
        elif command == "getState":
            return jsonify(
                isLightOn=self.light_controller.is_on,
                isPsuOn=self.psu_controller.is_on,
            )

    ##~~ Softwareupdate hook

    def get_update_information(self):
        return dict(
            printlight=dict(
                displayName="Print Light Plugin",
                displayVersion=self._plugin_version,
                type="github_release",
                user="tom0521",
                repo="OctoPrint-PrintLight",
                current=self._plugin_version,
                pip="https://github.com/tom0521/OctoPrint-PrintLight/archive/{target_version}.zip",
            )
        )


__plugin_name__ = "Print Light"
__plugin_version__ = "0.2.0"
__plugin_pythoncompat__ = ">=3.7,<4"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = PrintLightPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
