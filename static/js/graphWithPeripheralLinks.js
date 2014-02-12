function graphWithPeripheralLinks(width, height, jsondatavar, term, method, nodes) {

var format = d3.format(",d"),
    color = d3.scale.category20();

var svg = d3
    .select("#content")
	.append("svg")
    .attr("width", width)
    .attr("height", height);

var svg_key = d3
	.select("#key")
	.append("svg")
    .attr("width", d3.select("#sideLeft").style("width"))
    .attr("height", height/2);

var force = d3.layout.force()
    .gravity(0.7)
    .charge(-5000)
    .size([width, height]);

/*Array.prototype.contains = function(obj) {
	var i = this.length;
	while (i--) {
		if (this[i] === obj) {
			return true;
		}
	}
	return false;
}*/

// d3.json(jsondatafile, function(json) {

//json = JSON.parse(jsondatavar);
json = jsondatavar;

	// populates key
	var sizes = [];
	var groups = [];
	var cy = 10;
	for (var i=0;i<json.nodes.length;i++) {
		sizes[i] = json.nodes[i].size;
		if (json.nodes[i].group[0].groupnum !== 0) {
			for (var j=0;j<json.nodes[i].group.length;j++) {
				if ($.inArray(json.nodes[i].group[j].groupnum, groups) == -1) {
					groups.push(json.nodes[i].group[j].groupnum);
					svg_key.append("circle").attr("cx",20).attr("cy",cy).attr("r",6).attr("fill",color(groups.indexOf(json.nodes[i].group[j].groupnum)));
					svg_key.append("text").attr("x",30).attr("y",cy).attr("dy", ".3em").text(json.nodes[i].group[j].groupname);
					cy+=20;
				}
			}
		}
	}

	var interpNodeSize = d3.interpolateRound(10,75);
	function calcNodeSize(size) { return interpNodeSize((size-d3.min(sizes))/(d3.max(sizes)-d3.min(sizes))); }

    var coeff = [];
    for (i=0; i<json.links.length; i++) {
		coeff[i] = json.links[i].coefficient;
	}
	var interpLinkSize = d3.interpolateRound(0,15);
	function calcLinkSize(coeffInput) { return interpLinkSize((coeffInput-d3.min(coeff))/(d3.max(coeff)-d3.min(coeff))); }
	var interpLinkDistance = d3.interpolateRound(300,0);
	function calcLinkDistance(coeffInput) { return interpLinkDistance((coeffInput-d3.min(coeff))/(d3.max(coeff)-d3.min(coeff))); }

	force
        .nodes(json.nodes)
        .links(json.links)
        .linkStrength(function(d) { return calcLinkSize(d.coefficient)/40; })
        .start();

	var link = svg.selectAll(".link")
		.data(json.links)
	.enter().append("line")
		.attr("class", "link")
		.attr("x1", function(d) { return d.source.x; })
		.attr("y1", function(d) { return d.source.y; })
		.attr("x2", function(d) { return d.target.x; })
		.attr("y2", function(d) { return d.target.y; })
		.attr("stroke", "#C2C6D1")
		.attr("stroke-width", function(d) {
            linkSize = calcLinkSize(d.coefficient);
            return linkSize;
        })
		.on("mouseover", function(d) {d3.select(this).attr("stroke", "#000000"); mouseoverLink(d);})
        .on("mouseout", function(d) {d3.select(this).attr("stroke", "#C2C6D1"); mouseoutLink(d);});

	function mouseoverLink(d) {
		d3.select("#linkInfo-source").html("Frequency:<br>" + d.source.name + ": ");
		d3.select("#linkInfo-source-num").html(d.source.size);
		d3.select("#linkInfo-target").html(d.target.name + ": ");
		d3.select("#linkInfo-target-num").html(d.target.size);
		d3.select("#linkInfo-coeff").html("<br>Association strength:");
		d3.select("#linkInfo-coeff-num").html(d.coefficient.toFixed(5));
	}

	function mouseoutLink(d) {
		d3.select("#linkInfo-source").html("");
		d3.select("#linkInfo-source-num").html("");
		d3.select("#linkInfo-target").html("");
		d3.select("#linkInfo-target-num").html("");
		d3.select("#linkInfo-value").html("");
		d3.select("#linkInfo-value-num").html("");
		d3.select("#linkInfo-coeff").html("");
		d3.select("#linkInfo-coeff-num").html("");
	}

	var node = svg.selectAll(".node")
		.data(json.nodes)
	.enter().append("g")
		.attr("class", "node")
		.call(force.drag)
		.on("mouseover", function(d) {
            d3.select("#linkInfo-source").html("<i>Click to make this the central node.</i>");
            d3.select(this).attr("cursor", "pointer"); d3.select(this).attr("stroke", "#000000");
        })
		.on("mouseout", function(d) {
            d3.select("#linkInfo-source").html("");
            d3.select(this).attr("cursor", "default"); d3.select(this).attr("stroke", "none");
        })
		.on("click", function(d) {clickNode(d3.select(this).text());});

	svg.selectAll(".node")
		.filter(function(d,i) { return i === 0; })
		.on("mouseover", function(d) {d3.select(this).attr("cursor", "default"); d3.select(this).attr("stroke", "none");})
		.on("click", function(d) {return true;});

    function clickNode(text) {
        window.location.href = '/graph.do?q=' + text + '&metric=' + method + '&nodenum=' + nodes;
        ga('send', 'event', 'graph', 'node_click', term);
    }

	function generateArcPath() {
		return d3.svg.arc()
			.outerRadius(function(d) { return calcNodeSize(d3.select(this.parentNode).datum().size); })
			.innerRadius(0)
			.startAngle(function(d,i) { return i * 2*Math.PI / (d3.select(this.parentNode).datum().group.length); })
			.endAngle(function(d,i) { return (i+1) * 2*Math.PI / (d3.select(this.parentNode).datum().group.length); });
	}

	node.selectAll("path")
		.data(function(d) { return d.group; })
    .enter().append("path")
		.attr("d", generateArcPath())
		.style("fill", function(d) { if(d.groupnum === 0) {return "#000000";} else {return color(groups.indexOf(d.groupnum));} })
		.style("opacity", 0.7);

    svg.selectAll(".node")
		.filter(function(d,i) { return i === 0; })
		.append("circle")
			.attr("r", function(d) { return calcNodeSize(d.size); })
			.style("stroke", "#000000")
			.style("stroke-width", 3)
			.style("fill", "#FFFFFF");

	node.append("text")
		.attr("dy", ".3em")
		.style("text-anchor", "middle")
		.text(function(d) { return d.name; });

	force.on("tick", function() {
		link.attr("x1", function(d) { return d.source.x; })
			.attr("y1", function(d) { return d.source.y; })
			.attr("x2", function(d) { return d.target.x; })
			.attr("y2", function(d) { return d.target.y; });

		node.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });
	});
// });

}