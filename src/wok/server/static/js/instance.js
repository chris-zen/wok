function update(name) {
	$("#modules").css("font-weight", "bold").text("Loading state ...");
	$.getJSON("/api/monitoring/instance/" + name, function(data) {
		$("#modules").removeAttr("style").empty();
		$("#modules").modules_tree({data: data.root_node.modules, debug: false});
	}).error(function(jqXHR, error_type, exception) {
		$("#modules").css("font-weight", "bold").css("font-color", "red")
			.html(
				"<p>There was an error loading state !<p>" +
				"<p>" + error_type + "</p>" +
				exception !== undefined ? "<p>" + exception + "</p>" : ""
			);
	});
}