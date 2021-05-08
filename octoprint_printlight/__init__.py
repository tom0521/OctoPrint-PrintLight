# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import octoprint.printer

import RPi.GPIO as GPIO

from octoprint.events import Events

class PrintLightPlugin(octoprint.plugin.AssetPlugin,
                       octoprint.plugin.EventHandlerPlugin,
                       octoprint.plugin.SettingsPlugin,
                       octoprint.plugin.ShutdownPlugin,
                       octoprint.plugin.SimpleApiPlugin,
                       octoprint.plugin.TemplatePlugin):

    def __init__(self):
        self.isOn = False
        
        self.gpioPin = 0
        self.gpioInvert = False

    ##~~ Light Control Functions

    def turn_on(self):
        self._logger.debug("Turning print light on")
        self.isOn = True
        self._state_change()

    def turn_off(self):
        self._logger.debug("Turning print light off")
        self.isOn = False
        self._state_change()

    def toggle(self):
        self._logger.debug("Toggling light")
        self.isOn = not self.isOn
        self._state_change()

    def _state_change(self):
        self._plugin_manager.send_plugin_message(self._identifier, dict(isLightOn=self.isOn))
        GPIO.output(self.gpioPin, self.isOn ^ self.gpioInvert)

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

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpioPin, GPIO.OUT)
        self.turn_off()

    def get_settings_defaults(self):
	return dict(
	    gpio=1
	)

    ##~~ ShutdownPlugin mixin

    def on_shutdown(self):
        GPIO.cleanup()

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
__plugin_pythoncompat__ = ">=2.7,<3" # only python 2
#__plugin_pythoncompat__ = ">=3,<4" # only python 3
#__plugin_pythoncompat__ = ">=2.7,<4" # python 2 and 3

def __plugin_load__():
	global __plugin_implementation__
        __plugin_implementation__ = PrintLightPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
	    "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
        }

