$.widget("ui.modules_select", {
	options: {
		data: undefined
	},

	_renderModule: function(container, model, level) {
		if (model === undefined)
			model = this._model;
		if (level === undefined)
			level = 0;

		var nodeDiv = $('<div class="mod-sel-node"></div>').appendTo(container);

		var dataDiv = $('<div class="mod-sel-data"></div>').appendTo(nodeDiv);

		var rheadDiv = $('<div class="mod-sel-rhead"></div>').appendTo(dataDiv);

		$('<div class="mod-sel-margin"></div>').width(level * 10).appendTo(rheadDiv);

		var expanderDiv = $('<div class="mod-sel-expander"></div>').appendTo(rheadDiv);

		var hasChildren = model.children !== undefined && model.children.length > 0;

		if (hasChildren) {
			var childrenDiv = $('<div class="mod-sel-children"></div>').appendTo(nodeDiv);

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
		else {
			nodeDiv.addClass("mod-sel-selectable");
			var e = this.element;
			nodeDiv.click(function () {
				$(e).trigger("select", [model]);
			});
		}

		var m = model.data;

		$('<div class="mod-sel-name"></div>')
						.text(m.name)
						.attr("title", m.title || null)
						.appendTo(rheadDiv);

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

			node.expanded = node.expanded || true;
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

		if (!this._updated && this._model !== undefined) {
			this.element.empty();
			for (mindex in this._model) {
				var node = this._model[mindex];
				this._renderModule(this.element, node);
			}

			this._updated = true;
		}
	},

	_create: function() {
		this._updated = false;
		
		this.element.addClass("mod-sel");

		if (this.options.data !== undefined)
			this._model = this._updateModel(this.options.data);

		this.update();
	},

	_destroy: function() {
		this.element.empty();
	}
});