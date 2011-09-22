$.widget("ui.modules_tree", {
	options: {
		debug: false,
		data: undefined,
		model: undefined
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

	_module: function(container, model, m, level) {
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
			/*container = $(".mon-mod-children", mod_div);*/
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
	},

	_create: function() {
		var e = this.element;
		var d = this.options.data;

		var model = [];
		for (var i = 0; i < d.length; i++) {
			var m = d[i];

			var child = {};
			model.push(child);
			this._module(e, child, m);
		}

		this.options.model = model;
	},

	_destroy: function() {
		this.element.empty();
	}
})