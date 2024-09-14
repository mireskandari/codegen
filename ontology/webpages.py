""" Creates various webpages surrounding the ontology. """

from owlready2 import *
from pyvis.network import Network
import networkx as nx
import webbrowser as wb


class OntologyVisualizer:
	DEFAULT_HTML_PHYSICS_OPTIONS = {
		"physics": {
			"barnesHut": {
				"gravitationalConstant": -3500,
				"springLength": 200,
				"springConstant": 0.01
			},
			"minVelocity": 0.75
		}
	}

	def __init__(self, physics_options: dict=None):
		self.physics_options = self.DEFAULT_HTML_PHYSICS_OPTIONS if physics_options is None else physics_options
		
	def create_html(self, graph, write_path, show:bool=False):
		# Create the basic html File
		nt = Network('100vh', '100%', directed=True)
		nt.from_nx(graph)
		nt.set_options(f"var options = {self.physics_options}".replace("'", '"'))
		nt.write_html(str(write_path))

		# Inject custom code
		make_html_injection = """\t\tfunction make_html(html) {const container = document.createElement("div"); container.innerHTML = html; return container;}; nodes.forEach(function(node) {node.title = make_html(node.title)});edges.forEach(function(edge) {edge.title = make_html(edge.title)});\n"""
		text = open(write_path).readlines()
		for i, line in enumerate(text):
			if line.strip().startswith("edges = new vis.DataSet([{"):
				break
		text.insert(i+1, make_html_injection)
		open(write_path, 'w').writelines(text)
		
		# Display to user
		if show:
			wb.open(write_path)

		return write_path

class OntologyDocumentation:
	DEFAULT_TITLE = "Ontology Documentation"
	PAGE_START = lambda self: f"""
		<!DOCTYPE html>
		<html lang="en">
		<meta charset="UTF-8">
		<title>{self.title}</title>
		<meta name="viewport" content="width=device-width,initial-scale=1">
		<link rel="stylesheet" href="">
		<style>
		.collapsible {{
			background-color: #777;
			color: white;
			cursor: pointer;
			padding: 18px;
			width: 100%;
			border: none;
			text-align: left;
			outline: none;
			font-size: 15px;
		}}

		.active, .collapsible:hover {{
			background-color: #555;
		}}

		.content {{
			padding: 0 18px;
			display: none;
			overflow: hidden;
			background-color: #f1f1f1;
		}}

		.tooltip {{
			position: relative;
			display: inline-block;
			border-bottom: 1px dotted black;
		}}

		.tooltip .tooltiptext {{
			visibility: hidden;
			width: 400px;
			background-color: black;
			color: #fff;
			text-align: center;
			border-radius: 6px;
			padding: 5px 0;

			/* Position the tooltip */
			position: absolute;
			z-index: 1;
		}}

		.tooltip:hover .tooltiptext {{
			visibility: visible;
		}}
		</style>
		<script>
		function toggle(className, displayState){{
			var elements = document.getElementsByClassName(className);
			for (var i = 0; i < elements.length; i++) {{
					elements[i].style.display = displayState;
			}}
		}}
		</script>

		<body>
		<h2>{self.title}</h2>
		<button onclick="toggle('inherited', 'none')">Hide Inherited</button>
		<button onclick="toggle('inherited', 'block')">Show Inherited</button>
		<hr>
		<table>
	"""

	PAGE_END = lambda self: """
		</table>
		</body>
		<script>toggle('inherited', 'none')</script>
		</html>
	"""
	def __init__(self, title: str=DEFAULT_TITLE):
		self.title = title 

	def create_html(self, graph, write_path, show: bool=False):
		lines = [
			*self._table_of_contents(graph),
			*self._entities(graph),
		]

		with open(write_path, 'w') as f:
			f.write(self.PAGE_START())
			f.writelines(lines)
			f.write(self.PAGE_END())

		if show:
			wb.open(write_path)

	def _table_of_contents(self, graph):
		classes = sorted(list(graph.nodes))
		padding = max(len(n) for n in graph.nodes)

		lines = []
		lines.append("<h3>Table of Contents</h3>")
		current_module = None
		for c in classes:
			module = str(c).split('.')[0]
			if current_module != module:
				current_module = module
				lines.append(f"<b>{module}</b>")
			lines.append("<table>")
			lines.append(f"<tr><td style='text-indent:50px'><a href='#{str(c)}'>{str(c):{padding}}</a></td></tr>")
			lines.append('</table>')
		lines.append('<hr>')
		return lines

	def _entities(self, graph):
		# Not sure how this handles multiple inheritance or inferred classes yet.
		thick_hrule = "<hr style='height:5px;border:none;color:#333;background-color:#333;'>"
		left_arrow = ' &#8592; '
		padding = max(len(n) for n in graph.nodes)

		lines = ["<table>"]
		lines.append(thick_hrule)
		

		for name, node in graph.nodes.items():
			if node['type'] != 'entity':
				continue


			## 1. Title String
			ancestors_string = left_arrow + left_arrow.join([f"<a href='#{a}'>{a}</a>" for a in reversed(node['ancestors'])])
			title_string = f"<b style='font-size:150%;background-color:orange;'>{name.split('.')[-1]:{padding}}</b> {ancestors_string} ({len(node['ancestors'])})"
			lines.append(f"<tr><td id={name}>")
			lines.append(f"{title_string}")

			
			# 2. Definition String
			lines.append(f"<p style='font-size:120%;'><b style='background-color:orange;'>Definition:</b> {node['definition']}</p>")
			

			# 3. Assertion String
			# 4. Relations String
			# 5. Properties String
			lines.append('<hr>')
			for data_name, data_node in graph.nodes.items():
				if data_node['type'] != 'datatype':
					continue

				for entity_group in data_node['domain']:
					assert len(entity_group) == 1
				domain_entities = [entity_group[0] for entity_group in data_node['domain']]
				
				if name in domain_entities:
					lines.append("<span style='background-color:green'><b style='font-size:120%'>" + data_name.split('.')[-1] + '</b></span>' + (' (Common Key)' if len(domain_entities) > 1 else '') + '<br>')
					lines.append(data_node['description'].strip() + ('<br>' if data_node['description'].strip() else '') + '<br>')
					lines.append('<hr>')

			lines.append(thick_hrule)
			lines.append(f"</td></tr>")
		lines.append("</table>")
		return lines



		
