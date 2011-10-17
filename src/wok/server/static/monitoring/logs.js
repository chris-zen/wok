$.widget("ui.logs", {
	options: {
		instance_name: null,
		task_index: 0
	},

	show: function() {
		$(this.element).show();
	},

	hide: function() {
		$(this.element).hide();
	},

	render: function() {
		this.element.empty();
	},

	update: function(instance_state) {
		if (instance_state !== undefined) {
			this._instance_state = instance_state;

			if (!this._modSelUpdated) {
				this._modSelWidget.update(instance_state.root.modules);
				this._modSelUpdated = true;
			}
		}
	},

	_setOption: function(key, value) {
		switch (key) {
			case "task_index":
				this.options.task_index = value;
				$("#logs-task-index").val(value);
			break;
		}
	},

	_updateLogs: function(logs) {
		this._logs = logs;
		var content = $("#logs-content").empty();
		for (log_idx in logs) {
			var log = logs[log_idx];
			$('<p>'
					+ '<span class="f ts">' + log[0] + '</span>'
					+ '<span class="f nm">' + log[1] + '</span>'
					+ '<span class="f lv">' + log[2] + '</span>'
					+ '<span class="tx">' + log[3] + '</span></p>')
				.appendTo(content);
		}
	},

	_moduleSelected: function(module) {
		updating = true; //TODO
		wok.status.debug("Loading logs for " + module.name + " ...");

		var resource = instance_name + "/" + module.name + "/" + this.options.task_index;

		var self = this;
		$.getJSON("/api/monitoring/task/logs/" + resource, function(data) {
			if (data.ok) {
				wok.status.hide();
				self._updateLogs(data.logs);
				self._selectedModule = module.name
			}
			else {
				if (data.error !== undefined)
					wok.status.error(data.error);
				else
					wok.status.error("Unknown error loading status");
			}
			updating = false;
		}).error(function(jqXHR, error_type, exception) {
			wok.status.error("Connection error loading status: " + error_type);
			updating = false;
		});
	},

	_create: function() {
		this._instance_state = null;
		this._modSelUpdated = false;
		this._logs = null;
		this._selectedModule = null;

		var root = $(this.element);

		// module selection

		var self = this;

		this._modSelWidget = $("#logs-mod-sel", root).modules_select()
			.bind("select", function (event, module) {
				self._moduleSelected(module) })
			.data("modules_select");

		// filtering

		$("#logs-task-btn-first", root).button({ text: false, icons: { primary: "ui-icon-seek-first" } })
			.click(function() { });
		$("#logs-task-btn-prev", root).button({ text: false, icons: { primary: "ui-icon-seek-prev" } });
		$("#logs-task-btn-next", root).button({ text: false, icons: { primary: "ui-icon-seek-next" } });
		$("#logs-task-btn-end", root).button({ text: false, icons: { primary: "ui-icon-seek-end" } });

		$("#logs-task-index", root).val(this.options.task_index);

		$("#logs-search-clean", root).button({ text: false, icons: { primary: "ui-icon-circlesmall-close" } });

		// contents
		
		this.update();
	},

	_destroy: function() {
		this.element.empty();
	}
});