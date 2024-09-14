# hack since code is not a package yet.
import sys
import os
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from ontology.factory import ClassFactory
from pprint import pprint
from pathlib import Path
from owlready2 import *
import pandas as pd
import ast
import json
import os
import re
import glob


class OwlToOntologyJsonConverter:
	""" In WarrantySphere.owl, turn on the reasoner, export inferred axioms to "documentation/doc.owl".
		Select all options (eg: annotations) then run this file.
	"""
	def __init__(self, ontology_path):
		self.ontology_file = str(ontology_path)
		self.ontology = get_ontology(self.ontology_file).load()
		self.all_classes = sorted(list(self.ontology.classes()), key=lambda c: str(c))
		self.ranks = self.get_ranks(owl.Thing)

	@staticmethod
	def get_ranks(start):
		ranks = {}
		def get_next_level(cls, level):
			ranks[cls] = level
			sclasses = list(cls.subclasses())
			if sclasses:
				return [get_next_level(c, level+1) for c in sclasses]

		get_next_level(start, 0)
		return ranks

	def parse(self, save=None):
		def format(domain_or_range):
			l = list(map(str, domain_or_range))
			l = [list(filter(lambda c: c.strip() != "annotations.vs:null", map(str.strip, rng.split('|')))) for rng in l]
			return l

		def get_definition(e):
			e = getattr(e, 'definition', None)
			return e[0] if e else None

		entities = {}
		relations = {}
		for c in self.all_classes:
			# Basic
			entity = {}
			entity['Name'] = str(c)
			entity['Description'] = get_definition(c)
			entity['Ancestors'] = list(map(str, sorted(c.ancestors(), key=lambda a: self.ranks[a], reverse=True)[1:-1]))

			# Assertions
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
				prop = {str(p): p for p in self.ontology.properties()}[relationship]
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
				for op in filter(lambda op: any(str(x) in str(op.domain) for x in classes), self.ontology.object_properties()):
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
				for dp in filter(lambda dp: any(str(x) in str(dp.domain) for x in classes), self.ontology.data_properties()):
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
		bs = BeautifulSoup(open(self.ontology_file).read(), features="xml")
		definitions = bs.find('rdf:RDF')
		if definitions:
			for datatype in definitions.find_all("rdfs:Datatype", recursive=False):
				name = datatype["rdf:about"].rsplit('/', 1)[1].replace('#', '.')
				enumeration = [dict(enumerate(y.contents)).get(0, "") for y in datatype.find_all('first')]
				datatypes[name] = enumeration
		

		if save:
			base = save + '/'
			with open(base + "classes.json", 'w') as f:
				json.dump(entities, f, indent=4)

			with open(base + "relations.json", 'w') as f:
				json.dump(relations, f, indent=4)

			with open(base + "datatypes.json", 'w') as f:
				json.dump(datatypes, f, indent=4)

		return entities, relations, datatypes


class TypescriptToJsonConverter:
	# The entity files are found under warranty-sphere -> lib -> entities

	OLD = Path(__file__).parent / "entities" / "old"
	NEW = Path(__file__).parent / "entities" / "new"
	TS_ENTITY_SUFFIX = '.entity.ts'
	
	def __init__(self, download=True):
		if download:
			self.paths = self.store_entities_locally()
		else:
			self.paths = {}
			old_files = glob.glob(f"{self.OLD}/*{self.TS_ENTITY_SUFFIX}")

			for f in old_files:
				name = str(Path(f).name).replace(self.TS_ENTITY_SUFFIX, "")
				
				assert f.count('/old/') == 1
				self.paths[name] = {
					'old': f,
					'new': f.replace("/old/", "/new/"),
				}

	def get(self, entity_name, old=False):
		return self.paths[entity_name]['old' if old else 'new']

	def parse(self, entity):
		""" Returns a Json object representing a typescript file. """
		f = open(self.get(entity, old=True))

		reading = False
		reading_column = False
		
		entity = {}
		field = {}
		for line in f:
			line = line.strip()

			if line.startswith("export class"):  # BEGIN
				entity['name'] = line.split()[line.split().index("class") + 1]  # The word after class 
				entity['fields'] = []
				reading = True

			if reading:
				if reading_column: # END
					# Get field definition
					field["name"], properties = line.split("!")
					field["datatype"] = [s.strip() for s in properties.strip(":").strip(";").split('|')]
					
					entity['fields'].append(field)
					field = {}
					reading_column = False

				if line.startswith("@"):
					if line.startswith("@PrimaryColumn"):
						continue  # The caller needs to set the primary column, so don't include that here.

					# Get column type and parameters
					assert line[-1] == ')'
					import json5  # Why this?
					column_parameters = line[line.index('(')+1:-1]  # After first '(' to before the final char ')'.
					field["properties"] = json5.loads(column_parameters) if column_parameters else {}  # After first '(' to before the final char ')'.
					
					reading_column = True
		return entity

	@classmethod
	def store_entities_locally(cls):
		import shutil
		github = R"/mnt/c/Users/Nawar/Desktop/Tasks/Datasets/vectorsolv-dev/vectorsolv-dev/"
		warranty_sphere = github + "libs/projects/warranty-sphere/"

		paths = {}
		for path in map(Path, glob.iglob(warranty_sphere + f'**/*{cls.TS_ENTITY_SUFFIX}', recursive=True)):
			shutil.copy(path, cls.OLD / path.name)
			paths[path.name.replace(cls.TS_ENTITY_SUFFIX, "")] = {
				'old': cls.OLD / path.name,
				'new': cls.NEW / path.name,
			}
		return paths
			
class OntologyJsonToTypescriptConverter:
	def __init__(self, entities, relationships, datatypes):
		self.entities = entities
		self.relationships = relationships
		self.datatypes = datatypes

	@staticmethod
	def enums_to_string(cls):
		""" Generates the contents of a typeorm typescript file defining all enum datatypes in the ontology. """
		# Enums could also be defined inline I believe, but then they wouldn't (?) be accessible elsewhere.
		def string_to_python_variable(s):  # https://stackoverflow.com/questions/3303312/how-do-i-convert-a-string-to-a-valid-variable-name-in-python
			s = re.sub('[^0-9a-zA-Z_]', '', s)  # Remove invalid characters
			s = re.sub('^[^a-zA-Z_]+', '', s)   # Remove leading characters until we find a letter or underscore
			return s
		string = ""
		for name, values in cls.DATATYPES.items():
			string = f"export enum {name.replace('.', '_')} " + '{'
			for value in values:
				variable_name = string_to_python_variable(value)
				string += "\n\t" + f'{variable_name} = "{value}"'
			string += "\n}"
		return string

	def create_new_file(self, typescript_entity, ontology_entity):
		""" Updates the file containing the typescript_entity to match the ontology_entity. """

		# Assumes only 1 class definition per file.
		update = []
		reading_class = False
		ttj = TypescriptToJsonConverter()
		
		# Essentially, get the contents before the "export class statement"
		for line in open(ttj.get(typescript_entity, old=True)):
			if line.startswith("export class "):
				reading_class = True

			if reading_class:
				break
			else:
				update.append(line)
		
		# Add the version that loads it from json.
		update.extend([
			"export const person_Person = new EntitySchema(",
				json.dumps(self.parse(ontology_entity), indent=4),
			")"
		])
		with open(ttj.get(typescript_entity, old=False), 'w') as f:
			f.writelines(update)

		from pprint import pprint
		pprint(update)



	def parse(self, entity_identifier):
		""" This creates the json that can be used to create an new EntitySchema. 
			@see https://typeorm.io/separating-entity-definition
		"""
		# Note that this returns a json, so that it can be edited.
		# Column options (eg: nullable) is a buisness/technical decision and are therefore not
		# part of the ontology. Instead, the caller should modify the returned json.

		# TODO: In Protege, stop using xsd and create "vs" datatypes and all data properties
		# should be from this. We can assert this on compilation. Furthermore, we can assert
		# that each vs:datatype has a conversion here.

		# https://github.com/typeorm/typeorm/blob/master/docs/entities.md#user-content-column-types
		ontology_entity = self.entities[entity_identifier]
		type_mapping = {
			"<class 'str'>": "String",
			"<class 'int'>": "Int",
			"<class 'bool'>": "Boolean"
		}
		
		typeorm = {}
		typeorm["name"] = ontology_entity["Name"].split('.')[-1]
		typeorm["columns"] = {
			"id": {
	            "type": "String",
	            "primary": True,
	            "generated": True,
	        }
		}
		typeorm["relations"] = {}

		for op in ontology_entity["Relations"]:
			op_name = op["Name"].split('.')[-1]
			
			# Assert that there is only one value for the range. Supporting "or" is future work.
			op_range = op["Range"]
			try:
				assert len(op_range) == 1, (typeorm["name"], op_name, op_range)
				assert len(op_range[0]) == 1, (typeorm["name"], op_name, op_range)
				op_range = op_range[0][0]
				assert op_range.split('.')[-1] == "Person"

				typeorm["relations"][op_name] = {
					"type": "many-to-many",
					"target": op_range.split('.')[-1],
				}
			except AssertionError:
				pass
		
		for op in ontology_entity["Data"]:
			op_name = op["Name"].split('.')[-1]
			
			# Rename data types (this may change if custom vs:datatypes are defined)
			op_range = str(op["Range"])
			for f, t in type_mapping.items():
				op_range = op_range.replace(f, t)
			op_range = ast.literal_eval(op_range)

			# Assert that there is only one value for the range. Supporting "or" is future work.
			assert len(op_range) == 1, (typeorm["name"], op_name, op_range)
			assert len(op_range[0]) == 1, (typeorm["name"], op_name, op_range)
			op_range = op_range[0][0]
			
			if op_range in self.datatypes:  # Enum
				typeorm["columns"][op_name] = {  # How to inject a default value?
					"type": 'enum',
					"enum": op_range.replace('.', '_'),
				}
			else:
				typeorm["columns"][op_name] = {
					"type": op_range,
				}

		return typeorm


if __name__ == '__main__':
	from pprint import pprint
	print("Enums can be exported from the ontology to typeorm.")
	print(OntologyToTypeormConverter.enums_to_string(ClassFactory))
	print()

	print("The Person class can be represented in typeorm json:")
	pprint(OntologyToTypeormConverter.create_typeorm(ClassFactory.CLASSES["person.Person"]))
	x = """\
	import { EntitySchema } from "typeorm"
	export const person_Person = new EntitySchema(
		ClassFactory.create_typeorm(Json["person.Person"])
	)
	"""
	print("This could be used like this:")
	print(x)

    # I need to think about how to generate that dev.owl - I think it may be a manual process.

	# typescript = j2t.parse('dev.Customer')
	# print(typescript)
	# print()



	# Convert this object to the Class/Relations Json format. // Now I would have their typescript in the ontology format.
	# Then, in python the ontology loader can be used to load this as a dataset or class.
	# In theory, once a typescript converter is developed they could load it in.
	# Now, how does this get loaded into protege? ...


	# 1. Convert their customer class into protege
	# 2. Provide a typescript file that can drop-in replace the existing one.
	#        May have to manually create headers -> Actually, I should copy all the files to a directory.
	#        Then, remove the class definition, and replace it with the typescript_converter.py output.
	# 3. Repeat for all classes

	# Provide a folder with all the files, and ask him to try dropin replacing, and to see what happens.
	# Do the entities match? are these all the ones they need?


