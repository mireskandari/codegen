""" In WarrantySphere.owl, turn on the reasoner, export inferred axioms to "documentation/doc.owl".
	Select all options (eg: annotations) then run this file.
"""
from owlready2 import *

def get_ranks(start):
	ranks = {}
	def get_next_level(cls, level):
		ranks[cls] = level
		sclasses = list(cls.subclasses())
		if sclasses:
			return [get_next_level(c, level+1) for c in sclasses]

	get_next_level(start, 0)
	return ranks

title = "VectorSolv - Warranty Sphere Documentation"
start = f"""
<!DOCTYPE html>
<html lang="en">
<meta charset="UTF-8">
<title>{title}</title>
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
<h2>{title}</h2>
<button onclick="toggle('inherited', 'none')">Hide Inherited</button>
<button onclick="toggle('inherited', 'block')">Show Inherited</button>
<hr>
<table>
"""
end = """
</table>
</body>
<script>toggle('inherited', 'none')</script>
</html>
"""


def create_html(ontology_file, path):
	ontology_file = str(ontology_file)
	path = str(path)

	onto_path.append(".")
	ontology = get_ontology(ontology_file).load()

	all_classes = sorted(list(ontology.classes()), key=lambda c: str(c))
	r = get_ranks(owl.Thing)
	padding = max(len(str(p)) for p in all_classes)
	lines = []
	lines.append("<h3>Table of Contents</h3>")
	current_module = None
	for c in all_classes:
		module = str(c).split('.')[0]
		if current_module != module:
			current_module = module
			lines.append(module.title())
		lines.append("<table>")
		lines.append(f"<tr><td style='text-indent:50px'><a href='#{str(c)}'>{str(c):{padding}}</a></td></tr>")
		lines.append('</table>')
	lines.append('<hr>')

	lines.append("<table>")
	for c in all_classes:
		# Header
		# Not sure how this handles multiple inheritance or inferred classes yet.
		ancestors = sorted(c.ancestors(), key=lambda a: r[a])[:-1]
		ancestors_string = ' &#8592; ' + ' &#8592; '.join([f"<a href='#{a}'>{a}</a>" for a in reversed(ancestors[1:])])
		title_string = f"<b style='font-size:150%;background-color:orange;'>{str(c):{padding}}</b> {ancestors_string} ({r[c]-1})"
		lines.append(f"<tr><td id={str(c)}>")
		lines.append(f"{title_string}")
		lines.append(f"<p style='font-size:120%;'><b style='background-color:orange;'>Definition:</b> {c.definition.first()}</p>")
		
		# Assertions
		lines.append('<div>')
		lines.append(f"<p><b style='background-color:yellow;'>Assertions:</b></p>")
		assertions = [(p, '') for p in c.is_a if (p not in all_classes) and (p is not owl.Thing)] # I don't understand p not in all_classes.
		if assertions or c.equivalent_to:
			lines.append(f"<ul style='list-style-type: circle;'>")
			for clause in c.equivalent_to:
				assertions.append((str(clause).split('&')[1].strip(), '>'))
			
			for assertion, clause_type in assertions:
				assertion = str(assertion)
				assertion, cls = assertion[:-1].split('(')
				relationship, cardinality = assertion.rsplit('.', 1)
				if ',' in cls:
					cardinality += " " + cls.split(',')[0].strip()
					cls = cls.split(',')[1].strip()
				

				property_name = str(relationship)
				span_class = ''
				prop = {str(p): p for p in ontology.properties()}[relationship]
				if prop.definition.first():
					span_class = "class='tooltip'"
					property_name += f"<span class='tooltiptext'>{property_name}<hr>{prop.definition.first()}</span>"
				
				lines.append(f'<li><span {span_class}>(eq) {property_name}</span> | {cardinality} | <a href="#{cls}">{cls}</a></li>')
				# Does Owner have the Equivalent To clause? owns some Product
			lines.append(f"</ul>")
		lines.append('</div>')
		
		# Relations
		lines.append('<div>')
		for subtitle, classes in [('Inherited', ancestors), ('Derived', [c])]:
			lines.append(f"<span class='{subtitle.lower()}'><p><b style='background-color:cyan;'>Relations ({subtitle}):</b></p>")
			lines.append(f"<ul style='list-style-type: circle;'>")
			for op in filter(lambda op: any(str(x) in str(op.domain) for x in classes), ontology.object_properties()):
				property_name = str(op)
				span_class = ''
				if op.definition.first():
					span_class = "class='tooltip'"
					property_name += f"<span class='tooltiptext'>{property_name}<hr>{op.definition.first()}</span>"
				lines.append(f"<li><span {span_class}>{property_name}</span> &#8594; ["+', '.join([f"<a href='#{op.range}'>{r}</a>" for r in op.range])+"]</li>")
			lines.append("</ul></span>")
		lines.append('</div>')

		# Properties
		lines.append('<div>')
		for subtitle, classes in [('Inherited', ancestors), ('Derived', [c])]:
			lines.append(f"<span class='{subtitle.lower()}'><p><b style='background-color:lime;'>Properties ({subtitle}):</b></p>")
			lines.append("<ul>")
			for dp in filter(lambda dp: any(str(x) in str(dp.domain) for x in classes), ontology.data_properties()):
				rng = str(dp.range).replace('<', '&lt;').replace('>', '&gt;')[1:-1]
				rng = list(filter(lambda c: c.strip() != "annotations.vs:null", rng.split('|')))
				rng = list(filter(lambda c: c, rng))
				rng = f" &#8594; {'|'.join(rng)}" if rng else ''
				property_name = str(dp)
				span_class = ''
				if dp.definition.first():
					span_class = "class='tooltip'"
					property_name += f"<span class='tooltiptext'>{property_name}<hr>{dp.definition.first()}</span>"
				lines.append(f"<li><span {span_class}>{property_name}</span>" + rng + "</li>")
			lines.append("</ul></span>")
		lines.append('</div>')

		lines.append("<hr style='height:5px;border:none;color:#333;background-color:#333;'></tr></td>")
	lines.append("</table>")

	with open(path, 'w') as f:
		f.write(start)
		f.writelines(lines)
		f.write(end)

if __name__ == '__main__':
	from pathlib import Path
	create_html(
		Path(__file__).resolve().parent.parent.parent / "protege" / "sphere" / "doc.owl",
		Path(__file__).resolve().parent.parent.parent / "datamesh" / "webpages" / "documentation.html",
	)