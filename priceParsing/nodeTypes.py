import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from priceParsing.baseParser import BaseParser



class NodeTypes(BaseParser):
	"""
	Parsers current node types, or reads existing node types from csv file.
	"""
	def __init__(self, csvDir='csvFiles', loadCsv=False):
		"""
		:param loadCsv: True if to load existing data from csv file.
		"""
		csvFile = 'aws-nodeTypes.csv'
		super().__init__(csvDir=csvDir, csvFile=csvFile)
		self.csvDir = csvDir
		self.csvFile = csvFile
		self.loadCsv = loadCsv
		self.pageLink = 'https://aws.amazon.com/ec2/instance-types/'
		self.stepCount = 46

		self.df = None

		if not self.loadCsv:
			self.parseNodeTypesPrices()
		else:
			self.loadFromCsv()


	def printStep(self, stepNum, stepStr):
		"""
		Print the step summary.

		:param stepNum: The number of the current step.
		:param stepStr: The string to print for the step.
		"""
		print("[%i/%i]: %s" % (stepNum, self.stepCount, stepStr))

	def parseNodeTypesPrices(self):
		"""
		Parse the node types using the webpage.

		:return: A dataframe of the current defined node types.
		"""
		startTime = time.time()
		# Create web page driver
		options = Options()
		options.headless = True
		options.add_argument("--window-size=1920,1200")

		driver = webdriver.Chrome(options=options)
		driver.get(self.pageLink)

		# Get Tables
		tables = driver.find_elements_by_xpath("//table")
		self.printStep(1, "Found section Tables")

		# Parse Data From Tables
		data = []
		stepCount = 1
		for table in tables:
			tableSections = table.find_elements_by_xpath(".//tr")
			headerElements = tableSections[0].find_elements_by_xpath(".//th") + tableSections[0].find_elements_by_xpath(
				".//td")
			headers = [i.get_property('innerText').strip() for i in headerElements]

			for tableRow in tableSections[1:]:
				rowItems = [i.get_property('innerText') for i in tableRow.find_elements_by_xpath(".//td")]
				dataRow = {k: v for k, v in zip(headers, rowItems)}
				data.append(dataRow)

			stepCount += 1
			self.printStep(stepCount, "Parsed Table %i" % (stepCount - 1))


		# Convert to dataframe
		self.df = pd.DataFrame(data)
		# Clean dataframe
		self.df = self.cleanNodeTypesDataframe(self.df)
		self.df = self.df.set_index(['InstanceType'])

		# Write data to disc
		filename = os.path.join(self.csvDir, self.csvFile)
		self.df.to_csv(filename)
		print('Wrote ', filename)

		endTime = time.time()
		print('Elapsed %.2fs' % (endTime - startTime))

		return self.df

	def cleanNodeTypesDataframe(self, df):
		"""
		Clean the dataframe by renaming duplicate columns with different names.

		:param df: The dataframe to clean.
		:return: The cleaned dataframe.
		"""
		# Combine Instance Names
		df['Instance Size'].update(df['Instance'])
		df['Instance Size'].update(df['Instance size'])
		df['Instance Size'].update(df['Name'])
		df['Instance Size'].update(df['Model'])
		df = df.drop(columns=['Instance', 'Instance size', 'Name', 'Model'])

		# Combine Storage Information
		storageItems = ['Instance Storage',
		                'Instance Storage (GIB)',
		                'Instance Storage (GiB)',
		                'Storage (GB)',
		                'Instance Storage (GB)',
		                'Local Storage (GB)',
		                'Instance Storage (TB)']
		for item in storageItems:
			df['Storage'].update(df[item])
		df = df.drop(columns=storageItems)

		# Combine network numbers
		network = ['Network Bandwidth (Gbps)',
		           'Network Burst Bandwidth (Gbps)',
		           'Network Performance (Gbps)',
		           'Networking Performance (Gbps)',
		           'Networking Performance',
		           'Network Perf (Gbps)',
		           'Network bandwidth']
		for item in network:
			df['Network Bandwidth'].update(df[item])
		df = df.rename(columns={'Network Bandwidth': 'Network'})
		df = df.drop(columns=network)

		# Combine EBS numbers
		ebs = ['EBS Bandwidth (Mbps)',
		       'EBS Burst Bandwidth (Mbps)',
		       'Dedicated EBS Bandwidth (Mbps)',
		       'EBS Bandwidth (Gbps)',
		       'EBS Bandwidth (Gbps)',
		       'Dedicated EBS Bandwidth (Gbps)',
		       'Dedicated EBS Bandwidth',
		       'EBS bandwidth']
		for item in ebs:
			df['EBS Bandwidth'].update(df[item])
		df = df.drop(columns=ebs)

		# Combine vCPUs numbers
		vcpus = ['vCPUs',
		         'vCPU*',
		         'Logical Processors*']
		for item in vcpus:
			df['vCPU'].update(df[item])
		df = df.drop(columns=vcpus)

		# Combine credits per hour numbers
		credits = ['CPU Credits Earned / Hr',
		           'CPU Credits / hour']
		for item in credits:
			df['CPU Credits/hour'].update(df[item])
		df = df.drop(columns=credits)

		# Combine Memory numbers
		mem = ['RAM (GiB)',
		       'Mem(GiB)',
		       'Memory (GiB)']
		for item in mem:
			df['Mem (GiB)'].update(df[item])
		df = df.drop(columns=mem)

		# Combine GPU P2P numbers
		gpup2p = ['GPU Peer to Peer']
		for item in gpup2p:
			df['GPU P2P'].update(df[item])
		df = df.drop(columns=gpup2p)

		# Combine GPU Memory numbers
		gpumem = ['GPU Memory (GiB)']
		for item in gpumem:
			df['GPU Mem (GiB)'].update(df[item])
		df = df.drop(columns=gpumem)

		# Fix broken EBS column
		df['EBS Bandwidth'].update(df[df.columns[7]])
		df = df.drop(columns=[df.columns[7]])

		# Reorder Columns
		newColumnOrder = ['Instance Size', 'vCPU', 'Mem (GiB)', 'Storage', 'GPUs', 'GPU Mem (GiB)', 'EBS Bandwidth',
		                  'Network Performance', 'Network', 'Baseline Performance / vCPU', 'CPU Credits/hour',
		                  'GPUDirect RDMA', 'GPU P2P', 'Inferentia chips', 'Inferentia chip-to-chip interconnect',
		                  'FPGAs', 'Aggregate Disk Throughput (MiB/s)']
		df = df[newColumnOrder]

		# Convert some columns to numeric
		def removeStar(x):
			return str(x).replace('*', '').replace(',', '')

		df['vCPU'] = df['vCPU'].apply(removeStar)

		# Rename column for consistentcy
		df = df.rename(columns={"Instance Size": "InstanceType"})

		return df

