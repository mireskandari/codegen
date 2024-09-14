""" This file loads ontologies into a common graph format. """

import ontology
from pprint import pprint
from pathlib import Path
from owlready2 import *
import json
import networkx as nx

def owl_to_json(ontology_path):
	""" Returns a json representation of the ontology.

		ontology_path must be a single file ontology.
		In protege, turn on the reasoner, export inferred axioms to "something.owl".
		Select all options (eg: annotations) then run this function with it.
	"""

	def get_ranks(start):
		""" Returns the inheritance level in the hierarchy. """
		ranks = {}
		def get_next_level(cls, level):
			ranks[cls] = level
			sclasses = list(cls.subclasses())
			if sclasses:
				return [get_next_level(c, level+1) for c in sclasses]

		get_next_level(start, 0)
		return ranks

	ontology = get_ontology(str(ontology_path)).load()
	all_classes = sorted(list(ontology.classes()), key=lambda c: str(c))
	entities = {}
	r = get_ranks(owl.Thing)

	relations = {}
	for c in all_classes:
		def format(domain_or_range):
			l = list(map(str, domain_or_range))
			l = [list(filter(lambda c: c.strip() != "annotations.vs:null", map(str.strip, rng.split('|')))) for rng in l]
			return l

		def get_definition(e):
			e = getattr(e, 'definition', None)
			return e[0] if e else None

		entity = {}
		entity['Name'] = str(c)
		entity['Definition'] = get_definition(c)
		entity['Ancestors'] = list(map(str, sorted(c.ancestors(), key=lambda a: r[a], reverse=True)[1:-1]))

		entity['Assertions'] = []
		assertions = []		
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
			
			entity['Assertions'].append({
				'property': property_name,
				'cardinality': cardinality,
				'target': cls,
			})
			
		# Relations
		entity["Relations"] = []
		for subtitle, classes in [('Inherited', entity['Ancestors']), ('Derived', [c])]:
			for op in filter(lambda op: any(str(x) in str(op.domain) for x in classes), ontology.object_properties()):
				# Build relations list
				if str(op) not in relations:
					relations[str(op)] = {
						"Definition": get_definition(op),
						"Domain": format(op.domain),
						"Range": format(op.range)
					}

				# Also append to entity Relations
				entity['Relations'].append({
					"Name": str(op),
					"Definition": get_definition(op),
					# "Domain": format(op.domain),  # Don't need domain since this class is a domain.
					"Range": format(op.range),
				})

		# Properties
		entity["Data"] = []
		for dp in ontology.data_properties():
			domain_as_list = list(str(d) for d in dp.domain)
			if str(c) not in domain_as_list:
				continue

			# Append to entity Relations
			entity['Data'].append({
				"Name": str(dp),
				"Definition": get_definition(dp),
				"Domain": format(dp.domain),
				"Range": format(dp.range),
			})
		entities[entity["Name"]] = entity

	
	# Create custom datatype extractor since owlready2 doesn't seem to support this.
	# It is assumed that all data types are an enumeration.
	from bs4 import BeautifulSoup

	datatypes = {}
	bs = BeautifulSoup(open(ontology_path).read(), features="xml")
	definitions = bs.find('rdf:RDF')
	if definitions:
		for datatype in definitions.find_all("rdfs:Datatype", recursive=False):
			name = datatype["rdf:about"].rsplit('/', 1)[1].replace('#', '.')
			enumeration = [dict(enumerate(y.contents)).get(0, "") for y in datatype.find_all('first')]
			datatypes[name] = enumeration
	
	return entities, relations, datatypes


def json_to_graph(entities, relations, datatypes, include_orphan_nodes:bool=True):
	def remove_prefixed_classes(sentence):
		# Remove the prefixes
		sentence = ' '.join(w.split('.')[-1] for w in sentence.split(' '))

		# Replace 'a' with 'an' if there is a vowel.
		words = sentence.split(' ')
		if len(words) == 3:
			if words[1].endswith('a') and any(words[2].lower().startswith(vowel) for vowel in 'aeiou'):
				words[1] += 'n'
			sentence = ' '.join(words)

		return sentence
		

	# Populate an empty graph
	graph = nx.Graph()

	# Load other relationships (object properties)
	nodes_with_relations = set()
	for name, rel in relations.items():
		try:	# TODO: handle multiple classes
			assert len(rel['Domain']) == 1, name
			assert len(rel['Domain'][0]) == 1, name
			assert len(rel['Range']) == 1, name
			assert len(rel['Range'][0]) == 1, name
		except AssertionError:
			print(f"Skipping {name}")
			continue

		a = rel['Domain'][0][0]
		b = rel['Range'][0][0]
		graph.add_edge(a, b, color='blue', width=8, title=remove_prefixed_classes(f"{a} {name} {b}"))
		nodes_with_relations.add(a)
		nodes_with_relations.add(b)

	# Load is-a relationships (inheritence)
	for name, cls in entities.items():
		for ancestor in cls['Ancestors']:
			if any([
					include_orphan_nodes,
					name in nodes_with_relations,
					ancestor in nodes_with_relations,
				]):
				if any([
						name in nodes_with_relations,
						ancestor in nodes_with_relations,
					]):		
					nodes_with_relations.add(name)
					nodes_with_relations.add(ancestor)

				graph.add_edge(name, ancestor, color='black', width=4, title=remove_prefixed_classes(f"{name} is-a {ancestor}"))
				break # Only do first ancestor, this assumes order is perserved, I'm not sure it is.

		# Load assertions
		for assertion in cls['Assertions']:
			nodes_with_relations.add(name)
			nodes_with_relations.add(assertion['target'])
			title = remove_prefixed_classes(f"<b> {name}</b> {assertion['property']} {assertion['cardinality']} <b> {assertion['target']}</b>")
			graph.add_edge(name, assertion['target'], color='green', width=8, title=title)



	# Load all nodes
	colors = ['orange', 'yellow', 'purple', 'violet', 'blue', 'lime', 'grey', 'brown']
	for name, cls in entities.items():	
		if not (include_orphan_nodes or name in nodes_with_relations):
			continue

		graph.add_node(
			name, 
			label=name.split('.')[-1],
			color=colors[len(cls['Ancestors'])],
			title=(
				f'<u>{remove_prefixed_classes(cls["Name"])}</u>'
				f'<br>{cls["Definition"] if cls["Definition"] else ""}'
			),
			ancestors=cls['Ancestors'],
			definition=cls['Definition'],
			type="entity",
			size=24,
		)

		# Load data properties
		for data_property in cls['Data']:
			# Get information
			r = str(data_property["Range"])
			r = r.replace('"', '')
			r = r.replace("<", "&lt;").replace(">", "&gt;")
			d = (data_property["Definition"] if data_property["Definition"] else "").replace('\n', '<br>')

			# Get Color and Label
			data_property_label = data_property['Name'].split('.')[-1]
			data_property_color = "cyan"
			if ('#important' in d) or ('# important' in d):
				data_property_color = "red"
				data_property_label = '#-' + data_property_label + '-#'
			if len(list(data_property['Domain'])) > 1:
				data_property_color = "black"
				
			# Add to graph
			graph.add_node(
				data_property['Name'],
				label=data_property_label,
				type="datatype",
				domain=data_property['Domain'],
				description=d,
				title=(
					f'<u>{remove_prefixed_classes(data_property["Name"])}</u>  {r}'
					f'<br>'
					f'{d}'
				),
				color=data_property_color,
			)
			graph.add_edge(
				name, 
				data_property['Name'],
				color='brown',
				title=remove_prefixed_classes(f"{name} has-a {data_property['Name']}"),
			)

	return graph

if __name__ == '__main__':
	entities, relations, datatypes = get_ontology_json(str(Path(__file__).parent/"../../protege/sphere/doc.owl"))
	base = "../json/"
	with open(base+"classes.json", 'w') as f:
		json.dump(entities, f, indent=4)
	with open(base+"relations.json", 'w') as f:
		json.dump(relations, f, indent=4)
	with open(base+"datatypes.json", 'w') as f:
		json.dump(datatypes, f, indent=4)

	


