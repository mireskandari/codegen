import pandas as pd
import ontology.factory as factory

class Database:
	def __init__(self, df):
		self.df = df

	def load(self, other, **mapping):
		# 1) Rename other according to mapping and add it to self, should also validate datatypes.
		# 2) other gets sliced to the intersection between the two dfs (i.e. common headers)
		# 3) other is returned
		# *) Side Effect: self.df concats with other
		assert all(key in self.df for key in mapping), ("All mapping keys should be in the original dataframe.", set(mapping.keys()), set(self.df)) 
		other.rename(columns={v: k for k, v in mapping.items()}, inplace=True)
		other = other[list(set(self.df).intersection(set(other)))]
		self.df = pd.concat([self.df, other])
		return other


def create_database(ontology_entity, fields=None):
	# TODO: Implement fields, to take a subset of the entity's fields.
	cls = factory.ClassFactory(**ontology_entity)
	headers = list(map(lambda x: x["Name"].split('.')[-1], cls.Data))
	return Database(pd.DataFrame(columns=headers))

