$.widget("ui.modules", {
	options: {
		//data: undefined
	},

	show: function() {
		$(this.element).show();
	},

	hide: function() {
		$(this.element).hide();
	},

	/* TODO */
	expandAll: function(node) {
	},

	/* TODO */
	collapseAll: function(node) {
	},
	
	_renderModule: function(container, model, level) {
		if (model === undefined)
			model = this._model;
		if (level === undefined)
			level = 0;

		var nodeDiv = $('<div class="mod-st-node"></div>').appendTo(container);
		nodeDiv.data("model", model);

		var dataDiv = $('<div class="mod-st-data"></div>').appendTo(nodeDiv);

		var rheadDiv = $('<div class="mod-st-rhead"></div>').appendTo(dataDiv);

		$('<div class="mod-st-margin"></div>').width(level * 10).appendTo(rheadDiv);

		var expanderDiv = $('<div class="mod-st-expander"></div>').appendTo(rheadDiv);

		var hasChildren = model.children !== undefined && model.children.length > 0;

		if (hasChildren) {
			var childrenDiv = $('<div class="mod-st-children"></div>').appendTo(nodeDiv);

			var imgSrc = null;
			if (model.expanded) {
				imgSrc = "ui-icon-triangle-1-s"; // collapse
				childrenDiv.show();
			}
			else {
				imgSrc = "ui-icon-triangle-1-e"; // expand
				childrenDiv.hide();
			}

			expanderDiv
				.append('<span class="ui-icon ' + imgSrc + '"></span>')
				.click(function () {
					if (model.expanded) {
						$(this).children("span").removeClass().addClass("ui-icon ui-icon-triangle-1-e");
						childrenDiv.slideUp();
						model.expanded = false;
					}
					else {
						$(this).children("span").removeClass().addClass("ui-icon ui-icon-triangle-1-s");
						childrenDiv.slideDown();
						model.expanded = true;
					}
				});
		}

		var m = model.data;
		
		var idDiv = $('<div class="mod-st-id"></div>').appendTo(rheadDiv);
		$('<div class="mod-st-name"></div>').text(m.name).appendTo(idDiv);
		$('<div class="mod-st-title"></div>').text(m.title || "").appendTo(idDiv);

		var stateDiv = $('<div class="mod-st-state"></div>')
			.addClass("mon-state-bg-" + m.state).appendTo(dataDiv);
		$('<div class="mod-st-state-name"></div>').text(m.state).appendTo(stateDiv);
		$('<div class="mod-st-state-title"></div>').text(m.state_title || "").appendTo(stateDiv);
		
		var states = ["failed", "finished", "running", "queued", "submitted", "ready"];
		var total = 0;
		var count = {};
		var other = 0;
		for (var i = 0; i < states.length; i++)
			count[states[i]] = 0;

		var node_count = m.tasks_count;
		var node_count_type = "tasks";
		if (m.modules_count !== undefined) {
			node_count = m.modules_count;
			node_count_type = "modules";
		}

		for (state in node_count) {
			state_count = node_count[state];
			if ($.inArray(state, states) != -1)
				count[state] += state_count;
			else
				other += state_count;
			total += state_count;
		}

		var tasksDiv = $('<div class="mod-st-progress"></div>').appendTo(dataDiv);

		var total_percent = 0;
		var tasksBarDiv = $('<div class="mod-st-progress-bar"></div>').appendTo(tasksDiv);
		if (total > 0) {
			var last_percent_index = 0;
			var percents = [];
			for (i = 0; i < states.length; i++) {
				var state = states[i];
				var percent = Math.round((count[state] / total) * 100);
				percents.push(percent);
				total_percent += percent;
				if (percent > 0)
					last_percent_index = i;
			}

			if (other == 0)
				percents[last_percent_index] += 100 - total_percent;

			for (i = 0; i < states.length; i++) {
				state = states[i];
				$('<div class="mod-st-progress-base"></div>')
						.addClass("mon-state-bg-" + state)
						.width(percents[i] + "%")
						.attr("title", state + ": " + count[state])
						.appendTo(tasksBarDiv);
			}

			if (other > 0)
				$('<div class="mod-st-progress-base"></div>')
					.addClass("mon-state-bg-other")
					.width((100 - total_percent) + "%")
					.attr("title", "other: " + other)
					.appendTo(tasksBarDiv);
		}

		$('<div class="mod-st-progress-total"></div>')
			.text(total + " " + node_count_type)
			.appendTo(tasksDiv);

		if (hasChildren) {
			for (index in model.children)
				this._renderModule(
						childrenDiv,
						model.children[index],
						level + 1);
		}
	},

	_updateModel: function(data, model) {
		if (model === undefined || model === null)
			model = [];

		var upd_model = [];

		for (dindex in data) {
			var node = null;
			var data_node = data[dindex];

			if (dindex < model.length)
				node = model[dindex];
			else
				node = {};

			node.expanded = node.expanded || false;
			node.data = data_node;

			if (data_node.modules !== undefined && data_node.modules.length > 0)
				node.children = this._updateModel(data_node.modules, node.children);

			upd_model.push(node);
		}

		return upd_model;
	},

	update: function(data) {
		if (data !== undefined)
			this._model = this._updateModel(data.root.modules, this._model);
		
		if (this._model !== undefined) {
			this.body.empty();
			for (mindex in this._model) {
				var node = this._model[mindex];
				this._renderModule(this.body, node);
			}
		}
	},

	_create: function() {
		var e = this.element;
		/*this.message = $('<div class="mod-st-msg"></div>').appendTo(e);*/
		this.body = e; //$('<div class="mod-st-body"></div>').appendTo(e);

		/*if (this.options.data !== undefined)
			this._model = this._updateModel(this.options.data.root.modules);*/

		this.update();
	},

	_destroy: function() {
		this.element.empty();
	}
});