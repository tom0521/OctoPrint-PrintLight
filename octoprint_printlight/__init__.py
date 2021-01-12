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
                       octoprint.plugin.TemplatePlugin):

    ##~~ AssetPlugin

    def get_assets(self):
        return dict(
            js=["js/printlight.js"],
            css=["css/printlight.min.css"]
        )

    ##~~ EventHandlerPlugin mixin

    def on_event(self, event, payload):
        if event == Events.PRINT_STARTED:
            self._logger.debug("Print Light turning on pin %d" % self._settings.get_int(["gpio"]))
            GPIO.output(self._settings.get_int(["gpio"]), GPIO.HIGH)
            self._plugin_manager.send_plugin_message(self._identifier, dict(isLightOn=True))
        elif event in [Events.PRINT_DONE, Events.PRINT_FAILED, Events.PRINT_CANCELLED]:
            self._logger.debug("Print Light turning off pin %d" % self._settings.get_int(["gpio"]))
            GPIO.output(self._settings.get_int(["gpio"]), GPIO.LOW)
            self._plugin_manager.send_plugin_message(self._identifier, dict(isLightOn=False))

	##~~ SettingsPlugin mixin

    def on_settings_initialized(self):
        self._logger.debug("print light setting gpio pin %d to out" % self._settings.get_int(["gpio"]))
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._settings.get_int(["gpio"]), GPIO.OUT)

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
            dict(type="navbar", custom_bindings=False),
            dict(type="settings", custom_bindings=False)
        ]

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

