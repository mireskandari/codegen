""" In WarrantySphere.owl, turn on the reasoner, export inferred axioms to "documentation/doc.owl".
	Select all options (eg: annotations) then run this file.

	Deprecated, see ontology.loaders
"""
from pprint import pprint
from pathlib import Path
from owlready2 import *
import json

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

def get_ontology_json(ontology_path):  # Must be single file ontology
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
		entity['Description'] = get_definition(c)
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
		for subtitle, classes in [('Inherited', entity['Ancestors']), ('Derived', [c])]:
			for dp in filter(lambda dp: any(str(x) in str(dp.domain) for x in classes), ontology.data_properties()):
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

if __name__ == '__main__':
	entities, relations, datatypes = get_ontology_json(str(Path(__file__).parent/"../../protege/sphere/doc.owl"))
	base = "../json/"
	with open(base+"classes.json", 'w') as f:
		json.dump(entities, f, indent=4)
	with open(base+"relations.json", 'w') as f:
		json.dump(relations, f, indent=4)
	with open(base+"datatypes.json", 'w') as f:
		json.dump(datatypes, f, indent=4)

	


