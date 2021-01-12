$(function() {
	function PrintLightViewModel(paraeters) {
		var self = this;

		self.settings = parameters[0];
		
		self.isLightOn = ko.observable(undefined);
		self.indicator = $("#printlight_indicator");

		self.onStartup = function () {
			self.isLightOn.subscribe(function () {
				if (self.isLightOn()) {
					self.indicator.removeClass("off");
				} else {
					self.indicator.addClass("off");
				}
			});
		}

		self.onDataUpdatePluginMessage = function (plugin, data) {
			if (data.isLightOn !== undefined) {
				self.isLightOn(data.isLightOn);
			}
		}
	}
});
