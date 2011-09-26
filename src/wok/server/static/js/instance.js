var treeWidget = null;
var updating = false;

function update() {
	if (updating)
		return;

	updating = true;
	wok.status.debug("Loading status ...");

	$.getJSON("/api/monitoring/instance/" + instance_name, function(data) {
		treeWidget.update(data.root_node.modules);
		wok.status.hide();
		updating = false;
	}).error(function(jqXHR, error_type, exception) {
		wok.status.error("There was an error loading status !");
		updating = false;
	});
}

$(document).ready(function() {
	treeWidget = $("#modules").modules_tree().data("modules_tree");

	update();
	
	window.setInterval(update, 1000);
});