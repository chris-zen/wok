
var wok = wok || {
	status: {
		_last_msg: null,
		_last_level: null,

		debug: function(msg) {
			this.msg(msg, "debug");
		},

		info: function(msg) {
			this.msg(msg, "info");
		},

		warn: function(msg) {
			this.msg(msg, "warn");
		},

		error: function(msg) {
			this.msg(msg, "error");
		},

		hide: function(time) {
			$('#status-bar').hide(time);
		},

		msg: function(msg, level) {
			this._last_msg = msg;
			this._last_level = level;
			$('#status-bar')
				.removeClass()
				.addClass("status-bar-" + level)
				.text(msg)
				.show();
		}
	}
};
