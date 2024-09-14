""" This is the ontology module.

"""
import ontology.loaders as loaders
import ontology.webpages as webpages

class Ontology:
	@staticmethod
	def from_owl_file(ontology_file):
		entities, relationships, datatypes = loaders.owl_to_json(ontology_file)
		return Ontology.from_json(entities, relationships, datatypes)

	@staticmethod
	def from_json(entities, relationships, datatypes):
		return Ontology(loaders.json_to_graph(entities, relationships, datatypes))

	def __init__(self, graph):
		assert not isinstance(graph, str), "A string was passed to the constructor, did you mean '.from_owl_file()'?"
		self.graph = graph

	def create_visualization(self, write_path="ontology_visualizer.html", show=False):
		webpages.OntologyVisualizer().create_html(self.graph, write_path, show)

	def create_documentation(self, write_path="ontology_documentation.html", show=False, title="Ontology Documentation"):
		webpages.OntologyDocumentation(title).create_html(self.graph, write_path, show)

