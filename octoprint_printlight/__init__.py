# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import octoprint.printer

from flask import jsonify

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

try:
    import serial
except ImportError:
    serial = None

from octoprint.events import Events


class PrintLightPlugin(octoprint.plugin.AssetPlugin,
                       octoprint.plugin.EventHandlerPlugin,
                       octoprint.plugin.SettingsPlugin,
                       octoprint.plugin.ShutdownPlugin,
                       octoprint.plugin.SimpleApiPlugin,
                       octoprint.plugin.TemplatePlugin):

    def __init__(self):
        self.isOn = False

        self.controller = None
        self.gpioPin = 0
        self.gpioInvert = False
        self.serialPort = None
        self.serialBaudrate = 9600
        self._serialConnection = None
        self._gpioInitialized = False

    ##~~ Light Control Functions

    def turn_on(self):
        self._logger.debug("Turning print light on")
        self._state_change(True)

    def turn_off(self):
        self._logger.debug("Turning print light off")
        self._state_change(False)

    def toggle(self):
        self._logger.debug("Toggling light")
        self._state_change(not self.isOn)

    def _state_change(self, state):
        if self.controller == "gpio":
            GPIO.output(self.gpioPin, state ^ self.gpioInvert)
        elif self.controller == "usb_serial":
            try:
                self._serialConnection.write(b"ON\n" if state else b"OFF\n")
                self._serialConnection.flush()
            except (serial.SerialException, OSError, ValueError) as error:
                self._logger.error("Could not set USB relay state: %s", error)
                return
        else:
            self._logger.error("Cannot set light state because no controller is available")
            return

        self.isOn = state
        self._plugin_manager.send_plugin_message(self._identifier, dict(isLightOn=self.isOn))

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
            self._plugin_manager.send_plugin_message(self._identifier, dict(isLightOn=self.isOn))

    ##~~ SettingsPlugin mixin

    def on_settings_initialized(self):
        self.gpioPin = self._settings.get_int(["gpio"])
        self.gpioInvert = self._settings.get_boolean(["gpioInvert"])
        self.serialPort = self._settings.get(["serialPort"])
        self.serialBaudrate = self._settings.get_int(["serialBaudrate"])
        self._configure_controller(self._settings.get(["controller"]))

    def on_settings_save(self, data):
        super(PrintLightPlugin, self).on_settings_save(data)
        self.gpioPin = self._settings.get_int(["gpio"])
        self.gpioInvert = self._settings.get_boolean(["gpioInvert"])
        self.serialPort = self._settings.get(["serialPort"])
        self.serialBaudrate = self._settings.get_int(["serialBaudrate"])
        self._configure_controller(self._settings.get(["controller"]))

    def _configure_controller(self, controller):
        self._shutdown_controller()
        self.controller = None
        self.isOn = False

        if controller == "gpio":
            if GPIO is None:
                self._logger.error(
                    "GPIO control is selected, but RPi.GPIO is not installed"
                )
                return

            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpioPin, GPIO.OUT)
            self._gpioInitialized = True
            self.controller = controller
        elif controller == "usb_serial":
            if serial is None:
                self._logger.error(
                    "USB serial control is selected, but pyserial is not installed"
                )
                return

            try:
                self._serialConnection = serial.Serial(
                    port=self.serialPort,
                    baudrate=self.serialBaudrate,
                    timeout=1,
                    write_timeout=1
                )
            except (serial.SerialException, OSError, ValueError) as error:
                self._logger.error(
                    "Could not open USB relay on %s: %s", self.serialPort, error
                )
                return

            self.controller = controller
        else:
            self._logger.error("Unsupported light controller: %s", controller)
            return

        self.turn_off()

    def _shutdown_controller(self):
        if self._serialConnection is not None:
            self._serialConnection.close()
            self._serialConnection = None

        if self._gpioInitialized:
            GPIO.cleanup()
            self._gpioInitialized = False

    def get_settings_defaults(self):
        return dict(
            controller="gpio",
            gpio=1,
            gpioInvert=False,
            serialPort="/dev/ttyACM0",
            serialBaudrate=9600
        )

    ##~~ ShutdownPlugin mixin

    def on_shutdown(self):
        self._shutdown_controller()

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
            getState=[]
        )

    def on_api_get(self, request):
        return self.on_api_command("getState", [])

    def on_api_command(self, command, data):
        self._logger.debug("Api call")
        if command == 'turnOn':
            self.turn_on()
        elif command == 'turnOff':
            self.turn_off()
        elif command == 'toggle':
            self.toggle()
        elif command == 'getState':
            return jsonify(isLightOn=self.isOn)
        
    ##~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return dict(
            printlight=dict(
                displayName="Print Light Plugin",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="tom0521",
                repo="OctoPrint-PrintLight",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/tom0521/OctoPrint-PrintLight/archive/{target_version}.zip"
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
