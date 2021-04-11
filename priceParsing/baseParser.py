import os
import pandas as pd




class BaseParser:
	"""
	A base class to handle loading from disk.
	"""
	def __init__(self, csvDir='csvFiles', csvFile=None):
		self.csvDir = csvDir
		self.csvFile = csvFile
		self.df = None


	def loadFromCsv(self):
		"""
		Load existing prices from the csv file.
		:return: A dataframe of the current spot prices.
		"""
		filename = os.path.join(self.csvDir, self.csvFile)
		df = pd.read_csv(filename, index_col=0)

		self.df = df

		print('Read %s from disk.' % filename)

		return df
