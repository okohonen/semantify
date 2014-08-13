// namespace. 
if (typeof webannotator == "undefined") {  
	var webannotator = {};  
};  
 
// Grab passed in argument
webannotator = window.arguments[0];
 
webannotator.new_model = {
    selected: 0,
 
    populateMenus: function () {
	    var chooseMenu = document.getElementById("WebAnnotator_chooseModelSchemaMenu");
	    var deleteMenu = document.getElementById("WebAnnotator_chooseModelDeleteMenu");
	    
	    // chooseMenu.appendItem("Foo", 3);

	    if (webannotator.schemas.length == 0) {
	    	if (chooseMenu != null) {
	    		chooseMenu.setAttribute("disabled", "true");
		}
	    	if (deleteMenu != null) {
	    		deleteMenu.setAttribute("disabled", "true");
		}
	    } 
	    // if schema files are available, update menus
	    // and enable them
	    else {
	    	if (chooseMenu != null) {
		    chooseMenu.setAttribute("disabled", "false");
		    deleteMenu.setAttribute("disabled", "false");
	    	    // Remove all items from menus
		    var chooseNodes = document.getElementById('WebAnnotator_chooseModelSchemaMenu_pop');
		    var deleteNodes = document.getElementById('WebAnnotator_chooseModelDeleteMenu_pop');
	    	    while (chooseNodes.hasChildNodes()) {
	    		chooseNodes.removeChild(chooseNodes.firstChild);
	    	    }
	    	    while (deleteNodes.hasChildNodes()) {
	    		deleteNodes.removeChild(deleteNodes.firstChild);
	    	    }
	    		
	    	    // Add the names of the files in the menu: choose DTD and delete DTD
	    	    var i;
	    	    for (i = 0 ; i < webannotator.schemas.length ; i++) {
	    		var schema = webannotator.schemas[i];
	    		var menuitemChoose = chooseMenu.appendItem(schema["name"], i);
	    		menuitemChoose.setAttribute("id", "WebAnnotator_chooseModelSchemaMenu" + i);
	    		menuitemChoose.setAttribute("number", i);
	    		menuitemChoose.addEventListener("command", function(e) {webannotator.new_model.chooseFile(this.getAttribute('number'))});
			
			if (i == webannotator.new_model.selected) {
			    // Chosen one
			    chooseMenu.label = schema["name"];
			}
			
			var menuitemDelete = deleteMenu.appendItem(schema["name"], i);
	    		menuitemDelete.setAttribute("id", "WebAnnotator_chooseModelDeleteMenu" + i);
	    		menuitemDelete.setAttribute("number", i);
	    		menuitemDelete.addEventListener("command", function(e) {webannotator.new_model.deleteDTDFile(this.getAttribute('number'))});
			
		    }
	    	}
		
	    }
    },
    
    chooseFile: function (i) {
	var chooseMenu = document.getElementById("WebAnnotator_chooseModelSchemaMenu");
	chooseMenu.label = webannotator.schemas[i]["name"];	
    },

    deleteDTDFile: function (id) {
	// Check dtd is not in use
	var dtdFile = webannotator.schemas[id];

	var model;
	var i;
	for(i = 0; i < webannotator.models.length; i++){
	    model = webannotator.models[i];
	    if (model.dtd == dtdFile["name"]) {
		alert(webannotator.bundle.GetStringFromName("waSchemaAlreadyUsed"));
		return false;
	    }
	}

	webannotator.main.deleteFile(id);
	webannotator.new_model.populateMenus();
    },

    /**
     * Import a DTD file describing an annotation schema
     */
    importFile: function () {
	// File selection
	var nsIFilePicker = Components.interfaces.nsIFilePicker;
	var fileChooser = Components.classes["@mozilla.org/filepicker;1"].createInstance(nsIFilePicker);
	fileChooser.init(window, webannotator.bundle.GetStringFromName("waImportSelection"), nsIFilePicker.modeOpen);
	fileChooser.appendFilter(webannotator.bundle.GetStringFromName("waImportDTDFiles"),"*.dtd; *.DTD");    
	var res = fileChooser.show();
	if (res == nsIFilePicker.returnOK){		
	    var file = fileChooser.file;
	    var label = file.leafName;
	    
	    var error = webannotator.main.readDTDFile(file);		
	    
	    var str;
	    
	    if(error <= 0) {
		var i = 0;
		var j;
		var flag = -1;
		
		for(i =0; i < webannotator.schemas.length ; i++){
		    if(webannotator.schemas[i]["filename"] == label){
			flag = i;
			break;
		    }		
		}
		
		var ok = true;
		if(flag >= 0) {
		    ok = confirm(webannotator.bundle.GetStringFromName("waDuplicateImportConfirm1") + " " + label + " " + webannotator.bundle.GetStringFromName("waDuplicateImportConfirm2"));
		} 
		if (ok) {
		    var oldDTDFileName = webannotator.dtdFileName;
		    webannotator.dtdFileName = file.leafName;
		    var newSchema;
		    for (j=0; j < webannotator.schemas.length ; j++){
			webannotator.schemas[j]["lastused"] == "0";
		    }
		    // replace
		    if (flag >= 0) {
			newSchema = webannotator.schemas[i];
			newSchema["filename"] = webannotator.dtdFileName;
			newSchema["name"] = file.leafName;
			newSchema["lastused"] = "1";
			webannotator.currentSchemaId = i;
			if (typeof(webannotator.colors) != 'undefined' && webannotator.colors[webannotator.dtdFileName]) {
			    delete webannotator.colors[webannotator.dtdFileName];
			}
		    } 
		    // new
		    else {
			newSchema = {};
			newSchema["filename"] = webannotator.dtdFileName;
			newSchema["name"] = file.leafName;
			newSchema["lastused"] = "1";
			webannotator.schemas.push(newSchema);
			webannotator.currentSchemaId = webannotator.schemas.length - 1;
		    }
		    webannotator.main.createJSON();
		    webannotator.main.createCSS();
		    webannotator.main.writeSchemasFile();
		    webannotator.main.updateMenus(true, true);

		    webannotator.new_model.populateMenus();

		    webannotator.main.activate();
		    webannotator.main.options();
		}
	    }
	    else {
		alert("The format of the file " + file.leafName + " is not good!");
	    }
	}
	
    },

    create: function() {
	var s;
	var modelName = document.getElementById('model_name').value;
	if(modelName == "") {
	    alert(webannotator.bundle.GetStringFromName("waModelNameRequired"));
	    return false;
	}
	
	var chooseMenu = document.getElementById("WebAnnotator_chooseModelSchemaMenu");
	if (chooseMenu.disabled || chooseMenu.label == "-None-") {
	    alert(webannotator.bundle.GetStringFromName("waModelDTDRequired"));
	    return false;
	}

	// Check for pre-existing model with same name
	var model;
	var i;
	for(i = 0; i < webannotator.models.length; i++){
	    model = webannotator.models[i];
	    Application.console.log(model.name + " " + model.dtd)
	    if (modelName == model.name) {
		alert(webannotator.bundle.GetStringFromName("waModelExists"));
		return false;
	    }
	}
	var newModel = {name: modelName, dtd: chooseMenu.label, lastused: 0}
	webannotator.models.push(newModel)
	webannotator.main.updateMenus(true, true);

	// Activate the new model
	webannotator.main.chooseFile(webannotator.models.length - 1);

	return true;
    }
};

