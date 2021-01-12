$(function() {
	function PrintLightViewModel(parameters) {
		var self = this;

		self.isLightOn = ko.observable(false);
		
		self.indicator = $("#printlight_indicator");

		self.onStartup = function () {
			self.isLightOn.subscribe(function () {
				if (self.isLightOn()) {
					self.indicator.removeClass("off");
					self.indicator.children("i").removeClass("far").addClass("fas");
				} else {
					self.indicator.addClass("off");
					self.indicator.children("i").removeClass("fas").addClass("far");
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
