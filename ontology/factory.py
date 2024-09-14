"""
For anyone to integrate into this schema, they must implement a ClassFactory in their
language of choice. Below is an example in python.

	The ClassFactory must:
		1. Accept a dictionary in the format exported by owl_to_json.py representing an entity.
			That means a dictionary in this template: **load dynamically**
				Entity:
					Name: string
					Description: string
					Ancestors: list[string]
					Relations
						Name: string
						Definition: string
						Range: ???
					Data
						Name: string
						Definition: string
						Domain: ???
						Range: ???

				Domains are other entities and the range is a datatype from:
					BOOL
					STRING
					NUMBER
						INT
						DOUBLE
						CURRENCY
					DATETIME
						DATE
						TIME

		2. Expose the first level attributes (from the json above) as class attributes,
		    with the values equal to the json for those attributes:

		    Entity.Relations[0]["Name"] === "Entity"
		    |class attribute|  json   |     |string|

		3. Be a function object.
			This means when ClassFactory(entity_json) is called, the returned object can be called as a function.
			This function should return a *class* representing the entity:

			Entity = ClassFactory(entity_json)

			- This Entity must expose the data properties and relations as attributes.
				- Data properties and relations have a naming convention to prevent collisions.
				- relations are camelCase, data properties are Underscore_Title_Case **load dynamically**
		
		====================================================================================
		A. Add additional functionality through other means. This keeps the ClassFactory
		    straightforward and managable. Here are example use cases:

			- Adding Functions to a Class
				Note that relations are treated as lists with elements as
				other individuals. So they are not functions. If you wish to add a method
				(or other features) to a class produced from the ClassFactory, modify 
				the class after creation dynamically.
			
			- Creating Databases from a Class
			    This should be done elsewhere and take the class as input.

		B. Pass the test suite (that uses a json interface to provide language agnositic testing).
			[{
				"Test Name": string,
				"Description": string,
				"input": json,
				"output" json,
			}, ...]
		
"""
from ontology.converters.owl_to_json import get_ontology_json
from pathlib import Path
from pprint import pprint
import pandas as pd
import json
import os
import re

class ClassFactory:
	ONTOLOGY_PATHS = {
		"datascience": Path(__file__).resolve().parent.parent / "protege" / "sphere" / "doc.owl",
		"devteam": Path(__file__).resolve().parent.parent / "protege" / "devteam" / "dev.owl",
	}

	@classmethod
	def get_ontology(cls, ontology_name):
		path = cls.ONTOLOGY_PATHS[ontology_name]
		return get_ontology_json(path)

	@classmethod
	def from_named_ontology(cls, ontology_name, entity_name):
		ontology = cls.get_ontology(ontology_name)
		return cls.from_loaded_ontology(ontology, entity_name)

	@classmethod
	def from_loaded_ontology(cls, ontology, entity_name):
		entities, _, _ = ontology
		return cls(**entities[entity_name])

	def __init__(self, **entity_definition):
		# This allows the Class Factory to provide meta data about the class.
		self.__dict__.update(entity_definition)
		self.entity = entity_definition

	def __call__(self, **individual_parameters):  # Creating an individual
		class ObjectProperty(list):  # List wrapper that allows for custom attributes/functions.
			def __init__(self, rng, defin):
				super().__init__()  # Wrap empty list
				self.Range = rng
				self.Definition = defin

		# Create the initial form of an object for the requested entity.
		obj = type(self.entity["Name"].replace(".", "_"), (object, ), {})

		# Go through and add the object properties
		for relation in self.entity["Relations"]:
			name = relation["Name"].split('.')[-1]
			setattr(obj, name, ObjectProperty(relation["Range"], relation["Definition"]))

		## Go through and add the data properties
		# Make sure the user doesn't supply invalid arguments.
		for kw in individual_parameters:
			parameters = list(map(lambda x: x["Name"].split('.')[-1], self.entity['Data']))
			if kw not in parameters:
				raise ValueError(f"{kw} is not a valid parameter for the {obj.__name__} class.\nTry one of {parameters}")
		
		# Assign the data properties and the provided user values.
		obj.data = []
		for datum in self.entity["Data"]:
			name = datum["Name"].split('.')[-1]
			value = individual_parameters.get(name, None)  # Could do data type checking
			setattr(obj, name, value)
			obj.data.append(name)

		setattr(obj, "data_dict", lambda: pd.DataFrame([{h: getattr(obj, h) for h in obj.data}]))

		return obj


if __name__ == '__main__':
	# Create a Person class
	Person = ClassFactory.from_named_ontology("datascience", "person.Person")
	print(f"A {Person.Name} {Person.Description} They are decended from: {'->'.join(Person.Ancestors)}")
	print(f"There are {len(Person.Relations)} relationships modelled, and {len(Person.Data)} data attributes.")

	# Instances
	print("Here are some examples:")
	personA = Person(First_Name="jim", Language="English")
	personB = Person(First_Name="tom")
	personA.knows.append(personB)


	print(personA.First_Name, "speaks the", personA.Language, "language.")
	# print('The definition of "Language" is:', Person.Language.Definition)  # Not yet implemented.
	print(personA.First_Name, "knows:", list(map(lambda x: x.First_Name, personA.knows)))
	print('The definition of "knows" is:', personA.knows.Definition)

	
