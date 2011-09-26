$.widget("ui.modules_tree", {
	options: {
		data: undefined
	},

	/* TODO */
	expandAll: function(node) {
		var d = this.options.data;
		if (node === undefined) {
			for (mindex in d)
				this.expandAll(d[mindex]);
			return;
		}

		var model = node.data("model");
		if (model.isLeaf)
			return;
		else {
			for (mindex in model.children) {
				var child_model = model.children[mindex];
				if (!child_model.expanded) {
					var expander = $(".mon-mod-expander", node);
					expander.trigger("click");
				}
			}
		}
	},

	/* TODO */
	collapseAll: function(node) {
		var d = this.options.data;
		if (node === undefined) {
			for (mindex in d)
				this.expandAll(d[mindex]);
			return;
		}

		var model = node.data("model");
		if (model.isLeaf)
			return;
		else {
			for (mindex in model.children) {
				var child_model = model.children[mindex];
				if (child_model.expanded) {
					var expander = $(".mon-mod-expander", node);
					expander.trigger("click");
				}
				/*this.collapseAll(child)*/
			}
		}
	},

/*	_module: function(container, model, m, level) {
		if (level === undefined)
			level = 0;

		var mod_div = $("#mon-mod-template").clone().removeAttr("id");
		mod_div.data("data", m).data("model", model);

		$(".mon-mod-margin", mod_div).css("width", level * 10);
		
		if (m.modules !== undefined && m.modules.length > 0) {
			model.expanded = true;
			var expander = $(".mon-mod-expander", mod_div);
			expander.click(function () {
				expander.empty();
				if (model.expanded) {
					$("#mon-mod-expand").clone().removeAttr("id").appendTo(expander);
					$(".mon-mod-children", mod_div).slideUp();
					model.expanded = false;
				}
				else {
					$("#mon-mod-collapse").clone().removeAttr("id").appendTo(expander);
					$(".mon-mod-children", mod_div).slideDown();
					model.expanded = true;
				}
			});

			$("#mon-mod-collapse").clone().removeAttr("id").appendTo(expander);
		}
		
		$(".mon-mod-name", mod_div).text(m.name);

		state_class = "mon-mod-bg-" + m.state;
		$(".mon-mod-state-name", mod_div).addClass(state_class).text(m.state);
		$(".mon-mod-state-msg", mod_div).addClass(state_class).attr("title", m.state_msg).text(m.state_msg);

		var states = ["failed", "finished", "running", "queued", "submitted", "ready"];
		var total = 0;
		var count = {};
		var other = 0;
		for (var i = 0; i < states.length; i++)
			count[states[i]] = 0;

		for (state in m.tasks_count) {
			state_count = m.tasks_count[state];
			if ($.inArray(state, states) != -1)
				count[state] += state_count;
			else
				other += state_count;
			total += state_count;
		}

		var total_percent = 0;
		var tasksDiv = $(".mon-mod-tasks-bar", mod_div);
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
				$('<div class="mon-mod-tasks-base"></div>')
						.addClass("mon-mod-bg-" + state)
						.css("width", percents[i] + "%")
						.attr("title", state + ": " + count[state])
						.appendTo(tasksDiv);
			}

			if (other > 0)
				$('<div class="mon-mod-tasks-base"></div>')
					.addClass("mon-mod-bg-other")
					.css("width", (100 - total_percent) + "%")
					.attr("title", "other: " + other)
					.appendTo(tasksDiv);
		}

		$('.mon-mod-tasks-total', mod_div).text(total + " tasks");

		if (m.modules !== undefined && m.modules.length > 0) {
			var children = [];
			model.isLeaf = false;
			model.children = children;
			var parent_div = $('<div class="mon-mod-children"></div>').appendTo(mod_div);
			for (index in m.modules) {
				var child_model = {};
				children.push(child_model);
				this._module(
						parent_div,
						child_model,
						m.modules[index],
						level + 1);
			}
		}
		else
			model.isLeaf = true;

		if (this.options.debug)
			$("div", mod_div).addClass("mon-mod-debug")

		mod_div.appendTo(container);
	},*/
	
	_renderModule: function(container, model, level) {
		if (model === undefined)
			model = this._model;
		if (level === undefined)
			level = 0;

		var nodeDiv = $('<div class="mod-tree-node"></div>').appendTo(container);
		nodeDiv.data("model", model);

		var dataDiv = $('<div class="mod-tree-data"></div>').appendTo(nodeDiv);

		var rheadDiv = $('<div class="mod-tree-rhead"></div>').appendTo(dataDiv);

		$('<div class="mod-tree-margin"></div>').width(level * 10).appendTo(rheadDiv);

		var expanderDiv = $('<div class="mod-tree-expander"></div>').appendTo(rheadDiv);

		var hasChildren = model.children !== undefined && model.children.length > 0;

		if (hasChildren) {
			var childrenDiv = $('<div class="mod-tree-children"></div>').appendTo(nodeDiv);

			var imgSrc = null;
			if (model.expanded) {
				imgSrc = "/static/img/collapse.png";
				childrenDiv.show();
			}
			else {
				imgSrc = "/static/img/expand.png";
				childrenDiv.hide();
			}

			expanderDiv
				.append('<img src="' + imgSrc + '" alt="" />')
				.click(function () {
					if (model.expanded) {
						$(this).children("img").attr("src", "/static/img/expand.png");
						childrenDiv.slideUp();
						model.expanded = false;
					}
					else {
						$(this).children("img").attr("src", "/static/img/collapse.png");
						childrenDiv.slideDown();
						model.expanded = true;
					}
				});
		}

		var m = model.data;
		
		var idDiv = $('<div class="mod-tree-id"></div>').appendTo(rheadDiv);
		$('<div class="mod-tree-name"></div>').text(m.name).appendTo(idDiv);
		$('<div class="mod-tree-title"></div>').text(m.title || "").appendTo(idDiv);

		var stateDiv = $('<div class="mod-tree-state"></div>')
			.addClass("mod-tree-bg-" + m.state).appendTo(dataDiv);
		$('<div class="mod-tree-state-name"></div>').text(m.state).appendTo(stateDiv);
		$('<div class="mod-tree-state-title"></div>').text(m.state_title || "").appendTo(stateDiv);
		
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

		var tasksDiv = $('<div class="mod-tree-progress"></div>').appendTo(dataDiv);

		var total_percent = 0;
		var tasksBarDiv = $('<div class="mod-tree-progress-bar"></div>').appendTo(tasksDiv);
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
				$('<div class="mod-tree-progress-base"></div>')
						.addClass("mod-tree-bg-" + state)
						.width(percents[i] + "%")
						.attr("title", state + ": " + count[state])
						.appendTo(tasksBarDiv);
			}

			if (other > 0)
				$('<div class="mod-tree-progress-base"></div>')
					.addClass("mod-tree-bg-other")
					.width((100 - total_percent) + "%")
					.attr("title", "other: " + other)
					.appendTo(tasksBarDiv);
		}

		$('<div class="mod-tree-progress-total"></div>')
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
			this._model = this._updateModel(data, this._model);
		
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
		/*this.message = $('<div class="mod-tree-msg"></div>').appendTo(e);*/
		this.body = e; //$('<div class="mod-tree-body"></div>').appendTo(e);

		if (this.options.data !== undefined)
			this._model = this._updateModel(this.options.data);

		this.update();
	},

	_destroy: function() {
		this.element.empty();
	}
})