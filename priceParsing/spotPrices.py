from priceParsing.baseParser import BaseParser

import os
import time
import boto3
import pandas as pd



class SpotPrices(BaseParser):
	"""
	Parsers current spot prices, or reads existing spot prices from csv file.
	"""
	def __init__(self, apiKeyFilePath=None, csvDir='csvFiles', regionId='ap-southeast-2', subRegion='a', loadCsv=False):
		"""
		:param apiKeyFilePath: A path to the api key file.
		:param csvDir: The directory to read/write csv to/from.
		:param regionId: The region Id name, e.g. 'ap-southeast-2'.
		:param subRegion: The sub region string, e.g. 'a', 'b', 'c'.
		:param loadCsv: True if to load existing data from csv file.
		"""
		csvFile = 'aws-spot-prices-' + regionId + '-' + subRegion + '.csv'
		super().__init__(csvDir=csvDir, csvFile=csvFile)
		self.apiKeyFilePath = apiKeyFilePath
		self.csvDir = csvDir
		self.csvFile = csvFile
		self.regionId = regionId
		self.subRegion = subRegion
		self.loadCsv = loadCsv
		self.apiKeyFilePath = apiKeyFilePath

		self.df = None

		if not self.loadCsv:
			self.parseSpotPricesUsingAPI()
		else:
			self.loadFromCsv()


	def parseSpotPricesUsingAPI(self):
		"""
		Parse the current spot prices using the api.

		:return: A dataframe of the current spot prices.
		"""
		startTime = time.time()
		# Read keys file
		keys = pd.read_csv(self.apiKeyFilePath)
		print('Read keys file.')

		# Authenticate Client
		client = boto3.client('ec2', region_name=self.regionId,
							  aws_access_key_id=keys['Access key ID'].values[0],
							  aws_secret_access_key=keys['Secret access key'].values[0])

		# Get the spot price history
		prices = client.describe_spot_price_history(MaxResults=600,
													ProductDescriptions=['Linux/UNIX'],
													AvailabilityZone=self.regionId + self.subRegion)

		# Filter older updates
		instanceType = []
		keepData = []
		for price in prices['SpotPriceHistory']:
			newType = price['InstanceType']
			if newType not in instanceType:
				instanceType.append(newType)
				keepData.append(price)

		# Create dataframe
		self.df = pd.DataFrame(keepData)
		self.df = self.df.set_index(['InstanceType'])
		self.df['SpotPrice'] = self.df['SpotPrice'].astype(float)
		print('Read %i spot prices using api.' % self.df.shape[0])

		# Write data to disc
		filename = os.path.join(self.csvDir, self.csvFile)
		self.df.to_csv(filename)
		print('Wrote', filename)

		endTime = time.time()
		print('Elapsed %.2fs' %  (endTime - startTime))

		return self.df






