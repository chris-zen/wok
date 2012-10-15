$.widget("ui.icontrol", {
	options: {
	},

	_control: function(action) {
		this._control_updating = true;
		wok.status.debug(action + " ...");
		var self = this;
		$.getJSON("/api/monitoring/instance/control/" + this._instance.name + "?action=" + action, function(response) {
			if (response.ok && response.current_state !== undefined) {
				self._updateButtons(response.current_state);
				self._updateState(response.current_state);
				wok.status.hide();
			}
			else
				wok.status.error(response.error);
			this._control_updating = false;
		}).error(function(jqXHR, error_type, exception) {
			wok.status.error("Connection error: " + error_type);
			this._control_updating = false;
		});
	},

	_updateButtons: function(state) {

		var self = this;
		if (state == "running") {
			icon_name = "ui-icon-pause";
			start_func = function() { self._control("pause"); }
		}
		else {
			icon_name = "ui-icon-play";
			start_func = function() { self._control("start"); }
		}

		this._btn_start.button("option", "icons", { primary: icon_name })
						.unbind('click').click(start_func);

		var enabled = {start: false, stop: false, reset: false, reload: false};

		switch (state) {
			case "ready":
				enabled = {start: true, stop: false, reset: false, reload: true};
				break;
			case "running":
				enabled = {start: true, stop: true, reset: false, reload: false};
				break;
			case "paused":
				enabled = {start: true, stop: false, reset: true, reload: true};
				break;
			case "failed":
			case "finished":
			case "aborted":
				enabled = {start: true, stop: false, reset: true, reload: true};
				break;
		}

		this._btn_start.button("option", "disabled", !enabled.start);
		this._btn_stop.button("option", "disabled", !enabled.stop);
		this._btn_reset.button("option", "disabled", !enabled.reset);
		this._btn_reload.button("option", "disabled", !enabled.reload);
	},

	_updateState: function(state) {
		$("#icontrol-state", this.element)
			.removeClass()
			//.addClass("")
			.addClass("mon-state-bg-" + state)
			.text(state);
	},

	update: function(instance) {
		var prev_state = this._instance !== undefined ? this._instance.state : "";

		this._instance = instance;
		if (this._instance === undefined)
			return;
		
		if (prev_state != this._instance.state) {
			this._updateButtons(this._instance.state);
			this._updateState(this._instance.state);
		}

		var container = this.element;

		//$(container).attr("title", this._instance.name);

		var title = $("#icontrol-title", container);
		if (this._instance.title !== undefined)
			title.text(this._instance.title);
		else if (this._instance.name !== undefined)
			title.text(this._instance.name);
		if (this._instance.name !== undefined)
			title.attr("title", this._instance.name);
	},

	_create: function() {
		var container = this.element;

		var self = this;
		
		this._btn_start = $("#icontrol-btn-start", container).button(
			{ disabled: true, text: false, icons: { primary: "ui-icon-play" } })
			.attr("title", "Start execution")
			.hover(function(){ $(this).addClass("ui-state-hover"); },
					function(){ $(this).removeClass("ui-state-hover"); })
			.click(function() { self._control("start"); });

		this._btn_stop = $("#icontrol-btn-stop", container).button(
			{ disabled: true, text: false, icons: { primary: "ui-icon-stop" } })
			.attr("title", "Stop execution")
			.hover(function(){ $(this).addClass("ui-state-hover"); },
					function(){ $(this).removeClass("ui-state-hover"); })
			.click(function() { self._control("stop"); });

		this._btn_reset = $("#icontrol-btn-reset", container).button(
			{ disabled: true, text: false, icons: { primary: "ui-icon-arrowreturnthick-1-w" } })
			.attr("title", "Reset to the initial state")
			.hover(function(){ $(this).addClass("ui-state-hover"); },
					function(){ $(this).removeClass("ui-state-hover"); })
			.click(function() { self._control("reset"); });

		this._btn_reload = $("#icontrol-btn-reload", container).button(
			{ disabled: true, text: false, icons: { primary: "ui-icon-folder-open" } })
			.attr("title", "Reload workflow definition and configuration")
			.hover(function(){ $(this).addClass("ui-state-hover"); },
					function(){ $(this).removeClass("ui-state-hover"); })
			.click(function() { self._control("reload"); });
	},

	_destroy: function() {
		this.element.empty();
	}
})