$(function() {
	function PrintLightViewModel(parameters) {
		var self = this;

		self.isLightOn = ko.observable(false);
		
		self.indicator = $("#printlight_indicator");

		self.onStartup = function () {
			self.isLightOn.subscribe(function () {
				if (self.isLightOn()) {
					self.indicator.removeClass("off");
				} else {
					self.indicator.addClass("off");
				}
			});
		};

		self.onDataUpdaterPluginMessage = function (plugin, data) {
			if (plugin != "printlight") {
				return;
			}

			if (data.isLightOn !== undefined) {
				self.isLightOn(data.isLightOn);
			}
		};

	}

	OCTOPRINT_VIEWMODELS.push([
		PrintLightViewModel,
		["settingsViewModel"],
		["#navbar_plugin_printlight"]
	]);
});
