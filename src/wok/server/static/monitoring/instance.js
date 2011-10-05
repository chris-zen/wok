// widgets
var tabs = null;
var modStateWidget = null;
var logsModSel = null

var currentTab = "logs";

var updating = false;
var modSelUpdated = false;

function update() {
	if (updating)
		return;

	updating = true;
	wok.status.debug("Loading status ...");

	$.getJSON("/api/monitoring/instance/state/" + instance_name, function(data) {
		modStateWidget.update(data.root.modules);

		// update module selectors
		if (!modSelUpdated) {
			logsModSelWidget.update(data.root.modules);
			modSelUpdated = true
		}

		wok.status.hide();
		updating = false;
	}).error(function(jqXHR, error_type, exception) {
		wok.status.error("There was an error loading status !");
		updating = false;
	});
}

function tabChanged() {
	var selected = $("#tabs-buttons :checked").val();
	$("#tab-" + currentTab).hide();
	$("#tab-" + selected).show();
	currentTab = selected;
}

function logsModSelected() {
	
}

$(document).ready(function() {
	// tabs
	$("#tabs-body > div").addClass("tab").hide();
	$("#tab-btn-" + currentTab).attr("checked", "checked");
	$("#tabs-buttons").buttonset().change(tabChanged).trigger("change");

	// modules
	modStateWidget = $("#tab-modules").modules_state().data("modules_state");
	
	// logs
	logsModSelWidget = $("#tab-logs-mod-sel").modules_select()
		.bind("select", logsModSelected)
		.data("modules_select");

	$("#task-btn-first").button({ text: false, icons: { primary: "ui-icon-seek-first" } })
	$("#task-btn-prev").button({ text: false, icons: { primary: "ui-icon-seek-prev" } })
	$("#task-btn-next").button({ text: false, icons: { primary: "ui-icon-seek-next" } })
	$("#task-btn-end").button({ text: false, icons: { primary: "ui-icon-seek-end" } })

	update();
	
	window.setInterval(update, 2000);
});