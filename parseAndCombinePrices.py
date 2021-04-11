import os,sys, math
import pandas as pd

from priceParsing.spotPrices import SpotPrices
from priceParsing.definedDuration import DefinedDuration
from priceParsing.onDemand import OnDemand
from priceParsing.nodeTypes import NodeTypes



class AllPrices:
	"""
	Parse all prices into one convienient object.
	"""
	def __init__(self, apiKeyFilePath=None, csvDir='csvFiles', regionId='ap-southeast-2', subRegion='a'):
		"""
		:param apiKeyFilePath: A path to the api key file.
		:param csvDir: The directory to read/write csv to/from.
		:param regionId: The region Id name, e.g. 'ap-southeast-2'.
		:param subRegion: The sub region string, e.g. 'a', 'b', 'c'.
		"""
		self.apiKeyFilePath = apiKeyFilePath
		self.csvDir = csvDir
		self.mainCsvFile = "combined-prices-summary-%s.csv" % regionId
		self.regionId = regionId
		self.subRegion = subRegion

		self.spotPrices = None
		self.definedDurationPrices = None
		self.onDemandPrices = None
		self.nodeTypes = None

		self.df = None


	def parseAllPrices(self, spotPrices=True, definedDurationPrices=True, onDemandPrices=True, nodeTypes=True):
		"""
		Parse all prices and node types.

		:param spotPrices: True if we are to parse spot prices using the API, otherwise read from csv file.
		:param definedDurationPrices: True if we are to parse defined duration prices from the webpage, otherwise read from csv file.
		:param onDemandPrices: True if we are to parse on demand prices from the webpage, otherwise read from csv file.
		:param nodeTypes: True if we are to parse node types from the webpage, otherwise read from csv file.
		:return: A dataframe of combined price and type data.
		"""
		# Parse spot prices
		self.printHeader('Spot Prices Using Api', leadingNewLine=False)
		self.spotPrices = SpotPrices(apiKeyFilePath=self.apiKeyFilePath, csvDir=self.csvDir, regionId=self.regionId,
		                             subRegion=self.subRegion, loadCsv=not spotPrices)

		# Parse Defined Duration Spot Prices
		self.printHeader('Defined Duration Spot Prices Using Webpage')
		self.definedDurationPrices = DefinedDuration(csvDir=self.csvDir, regionId=self.regionId, loadCsv=not definedDurationPrices)

		# Parse On-Demand Prices
		self.printHeader('On-demand Prices Using Webpage')
		self.onDemandPrices = OnDemand(csvDir=self.csvDir, regionId=self.regionId, loadCsv=not onDemandPrices)

		# Parse Node Types Prices
		self.printHeader('Node Types Using Webpage')
		self.nodeTypes = NodeTypes(csvDir=self.csvDir, loadCsv=not nodeTypes)

		self.printHeader('Completed')

		# Generate the dataframes
		self.generateDataFrame()


	def generateDataFrame(self):
		"""
		Generate the dataframe from the data.

		:return: A generated dataframe of the combined data.
		"""
		# Spot Prices
		dfSpot = self.spotPrices.df
		# Defined Duration
		dfDefDur = self.definedDurationPrices.df
		# On-Demand Prices
		dfOnDem = self.onDemandPrices.df
		dfOnDem = dfOnDem[['Linux/UNIX Usage']]
		dfOnDem = dfOnDem.rename(columns={'Linux/UNIX Usage': 'On-Demand'})
		# Node Types
		dfNodeTypes = self.nodeTypes.df
		dfNodeTypes = dfNodeTypes[['vCPU', 'Mem (GiB)', 'Storage', 'GPUs', 'GPU Mem (GiB)', 'EBS Bandwidth']]

		# Merge dataframes
		df = pd.concat([dfSpot, dfDefDur, dfOnDem, dfNodeTypes], axis=1)

		# Calculate price proportions
		df['SpotProp%'] = 100.0 * df['SpotPrice'] / df['On-Demand']
		df['1Hr%'] = 100.0 * df['1-Hour Reserved'] / df['On-Demand']
		df['6Hr%'] = 100.0 * df['6-Hour Reserved'] / df['On-Demand']
		df = df[['GroupType', 'SpotPrice', '1-Hour Reserved', '6-Hour Reserved', 'On-Demand', 'SpotProp%', '1Hr%', '6Hr%',
		         'vCPU', 'Mem (GiB)', 'Storage', 'GPUs', 'GPU Mem (GiB)', 'EBS Bandwidth']]
		# Set dp display
		pd.options.display.float_format = '{:,.2f}'.format
		# Adjust index
		df2 = df.reset_index()
		df2 = df2.set_index(['GroupType', 'index'])
		self.df = df2

		# Write data to disc
		filename = os.path.join(self.csvDir, self.mainCsvFile)
		self.df.to_csv(filename)
		print('Wrote', filename)

		return self.df


	def getDataframe(self):
		"""
		Get the combined dataframe.

		:return: The combined dataframe.
		"""
		return self.df


	def printHeader(self, str='Test', allLen=100, leadingNewLine=True):
		"""
		Print a header with the name str.

		:param str: The string to print.
		:param allLen: The length of the header.
		:param leadingNewLine: True if a blank line is to be printed first.
		"""
		strLen = len(str)
		remainLen = allLen - strLen - 2
		halfLen1 = math.floor(remainLen / 2.0)
		halfLen2 = remainLen - halfLen1

		if leadingNewLine: print("")
		print('='*halfLen1, str, '='*halfLen2)




if __name__ == '__main__':
	# Region settings
	regionId = 'ap-southeast-2'
	subRegion = 'a'
	loadCsv = False

	# Set key path
	apiKeyFilePath = sys.argv[1]

	# Create parser
	allPrices = AllPrices(apiKeyFilePath=apiKeyFilePath, csvDir='csvFiles', regionId=regionId, subRegion=subRegion)
	allPrices.parseAllPrices(spotPrices=True, definedDurationPrices=True, onDemandPrices=True, nodeTypes=True)
	#allPrices.parseAllPrices(spotPrices=True, definedDurationPrices=False, onDemandPrices=False, nodeTypes=False)

	print(allPrices.getDataframe())

