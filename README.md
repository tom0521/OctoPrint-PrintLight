# OctoPrint-PrintLight

This plugin adds functionality for a light to be controlled throught the Raspberry Pi GPIO. A button/status 
indicator will be added to the navbar and the light will turn on while the printer is printing unless intentionally
turned off.

This is an adaptation of the PSUControl Plugin

## Setup

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/tom0521/OctoPrint-PrintLight/archive/master.zip

## Configuration

To set up this plugin, just select the GPIO pin that the light will be controlled by.

## TODO:

- [X] Invert the signal
- [X] Working navbar status indicator
- [X] API
- [X] Working button
- [ ] Use periphery library
- [ ] Send client light status on opened
- [ ] Add user permissions
