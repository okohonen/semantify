// Adapted for Scrapbook extension
// See license.txt for terms of usage

/********** add tag for selected text ***********/
var sbHighlighter = {
	nodePositionInRange : {
		SINGLE	: 0,
		START	: 1,
		MIDDLE	: 2,
		END		: 3
	},
	
	set : function(aSelection, aAttributes)	{
		var aNodeName = "span";
		var aWindow = content.window;
		for ( var r = 0; r < aSelection.rangeCount; ++r ) {
			var range = aSelection.range[r]; 
			var doc	  = aWindow.document;

			var startC	= range.startContainer;
			var endC	= range.endContainer;
			var sOffset	= range.startOffset;
			var eOffset	= range.endOffset;

			var sameNode = ( startC == endC );

			if ( ! sameNode || ! this._isTextNode( startC ) ) { 

				var nodeWalker 
					= doc.createTreeWalker(
							range.commonAncestorContainer,
							NodeFilter.SHOW_TEXT,
							this._acceptNode,
							false
					  );

				nodeWalker.currentNode = startC; 

				for ( var txtNode = nodeWalker.nextNode(); 
					  txtNode && txtNode != endC; 
					  txtNode = nodeWalker.nextNode() 
					) {
					if (txtNode.length > 0) {
						nodeWalker.currentNode 
							= this._wrapTextNodeWithSpan(
								doc,
								txtNode,
								this._createNode( 
									aWindow, 
									aNodeName, 
									aAttributes, 
									this.nodePositionInRange.MIDDLE 
								)
							); 
					}
				}
			}

			if ( this._isTextNode( endC ) ) 
				endC.splitText( eOffset );
			
			if ( ! sameNode && endC.length > 0) 
				this._wrapTextNodeWithSpan(
						doc,
						endC,
						this._createNode( 
							aWindow, 
							aNodeName, 
							aAttributes,
							this.nodePositionInRange.END
						)
				); 

			if ( this._isTextNode( startC ) ) { 
				var secondHalf = startC.splitText( sOffset );
				if (secondHalf.length > 0) {
					if ( sameNode ) {
						this._wrapTextNodeWithSpan(
							doc,
							secondHalf,
							this._createNode( 
								aWindow, 
								aNodeName, 
								aAttributes,
								this.nodePositionInRange.SINGLE
							)
						);
					}
					else {
						this._wrapTextNodeWithSpan(
							doc,
							secondHalf,
							this._createNode( 
								aWindow, 
								aNodeName, 
								aAttributes,
								this.nodePositionInRange.START
							)
						);
					}
				}
			} 

			range.collapse( true ); 

		}

	},

	_isTextNode : function( aNode ) 
	{ 
		return aNode.nodeType == aNode.TEXT_NODE; 
	},

	_acceptNode : function( aNode ) 
	{
		if ( aNode.nodeType == aNode.TEXT_NODE 
			 && ! ( /[^\t\n\r ]/.test( aNode.nodeValue ) ) 
		   )
			return NodeFilter.FILTER_REJECT;

		return NodeFilter.FILTER_ACCEPT;
	},

	_createNode : function( aWindow, aNodeName, aAttributes, aNodePosInRange )
	{
		var newNode = aWindow.document.createElement( aNodeName );
		for ( var attr in aAttributes )
		{
			newNode.setAttribute( attr, aAttributes[attr] );
		}
		newNode.addEventListener("mouseover", webannotator.main.showEdit);
		newNode.addEventListener("mouseout", webannotator.main.hideEdit);
		return newNode;
	},

	_wrapTextNodeWithSpan : function( aDoc, aTextNode, aSpanNode ) 
	{
		var clonedTextNode = aTextNode.cloneNode( false );
		var nodeParent	 = aTextNode.parentNode;	

		aSpanNode.appendChild( clonedTextNode );
		nodeParent.replaceChild( aSpanNode, aTextNode );

		return clonedTextNode;
	},

};

