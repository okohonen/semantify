// namespace. 
if (typeof webannotator == "undefined") {  
	var webannotator = {};  
};  
 
 
webannotator.new_model = {
    selected: 0,
 
    populateMenu: function () {
	    var chooseMenu = document.getElementById("WebAnnotator_chooseModelSchemaMenu");
	    
	    // chooseMenu.appendItem("Foo", 3);

	    if (webannotator.schemas.length == 0) {
	    	if (chooseMenu != null) {
	    		chooseMenu.setAttribute("disabled", "true");
		}
	    } 
	    // if schema files are available, update menus
	    // and enable them
	    else {
	    	if (chooseMenu != null) {
		    chooseMenu.setAttribute("disabled", "false");
	    		// Remove all items from menus
		        var chooseNodes = document.getElementById('WebAnnotator_chooseModelSchemaMenu_pop');
	    		while (chooseNodes.hasChildNodes()) {
	    			chooseNodes.removeChild(chooseNodes.firstChild);
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
			}
	    	    }
		
	    }
	},
    
    chooseFile: function (i) {
	webannotator.new_model.selected = i;
	var chooseMenu = document.getElementById("WebAnnotator_chooseModelSchemaMenu");
	chooseMenu.label = webannotator.schemas[i]["name"];
	
    }
};

