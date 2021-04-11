import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from priceParsing.baseParser import BaseParser



class DefinedDuration(BaseParser):
	"""
	Parsers current reserved duration prices, or reads existing reserved duration prices from csv file.
	"""
	def __init__(self, csvDir='csvFiles', regionId='ap-southeast-2', loadCsv=False):
		"""
		:param csvDir: The directory to read/write csv to/from.
		:param regionId: The region Id name, e.g. 'ap-southeast-2'.
		:param loadCsv: True if to load existing data from csv file.
		"""
		csvFile = 'aws-defined-duration-spot-prices-' + regionId + '.csv'
		super().__init__(csvDir=csvDir, csvFile=csvFile)
		self.csvDir = csvDir
		self.csvFile = csvFile
		self.regionId = regionId
		self.loadCsv = loadCsv
		self.pageLink = 'https://aws.amazon.com/ec2/spot/pricing/'
		self.stepCount = 15

		self.df = None

		if not self.loadCsv:
			self.parseDefinedDurationPrices()
		else:
			self.loadFromCsv()


	def printStep(self, stepNum, stepStr):
		"""
		Print the step summary.

		:param stepNum: The number of the current step.
		:param stepStr: The string to print for the step.
		"""
		print("[%i/%i]: %s" % (stepNum, self.stepCount, stepStr))

	def parseDefinedDurationPrices(self):
		"""
		Parse the defined duration prices using the webpage.

		:return: A dataframe of the current defined duration prices.
		"""
		startTime = time.time()
		# Create web page driver
		options = Options()
		options.headless = True
		options.add_argument("--window-size=1920,1200")

		driver = webdriver.Chrome(options=options)
		driver.get(self.pageLink)

		# Click Linux Defined Duration Button
		onDemandButton = driver.find_elements_by_xpath(".//a[contains(text(), 'Defined Duration for Linux')]")[0]
		onDemandButton.click()
		self.printStep(1, "Found OS Selection Button")

		# Select Region
		# Get section only containing one of these buttons
		singleSection = driver.find_elements_by_xpath(".//h4[contains(text(), 'Defined Duration for Linux')]")[0].find_element_by_xpath("./..")
		self.printStep(2, "Found Selection Selector")
		# Wait for dropdown to appear
		WebDriverWait(singleSection, 5).until(EC.presence_of_element_located((By.XPATH, ".//div[@class='dropdown-wrapper inline']"))).click()
		# Click region
		singleSection.find_element_by_xpath(".//li[@data-value='%s']" % self.regionId).click()
		self.printStep(3, "Selected Region Dropdown")

		# Get Tables
		tableGroup = singleSection.find_element_by_xpath(".//div[@class='content reg-%s']" % self.regionId)
		tables = tableGroup.find_element_by_xpath(".//table")
		self.printStep(4, "Found section Tables")

		# Parse Data From Tables
		data = []
		subTables = tables.find_elements_by_xpath(".//tbody")
		stepCount = 4
		for subTable in subTables:
			rows = subTable.find_elements_by_xpath(".//tr")
			headRow = subTable.find_elements_by_xpath(".//th")
			if len(headRow) > 0:
				groupType = headRow[0].text
				for row in rows[1:]:
					# Parse columns
					cols = row.find_elements_by_xpath(".//td")
					nodeType = cols[0].text
					reserved1Hour = float(cols[1].text.replace("$", "").replace(" per Hour", ""))
					reserved6Hour = float(cols[2].text.replace("$", "").replace(" per Hour", ""))

					# Store data
					rowData = [nodeType, groupType, reserved1Hour, reserved6Hour]
					data.append(rowData)

			stepCount += 1
			self.printStep(stepCount, "Parsed Table %i" % (stepCount - 4))

		# Convert to dataframe
		self.df = pd.DataFrame(data, columns=['InstanceType', 'GroupType', '1-Hour Reserved', '6-Hour Reserved'])
		self.df['1-Hour Reserved'] = self.df['1-Hour Reserved'].astype(float)
		self.df['6-Hour Reserved'] = self.df['6-Hour Reserved'].astype(float)
		self.df = self.df.set_index(['InstanceType'])

		# Write data to disc
		filename = os.path.join(self.csvDir, self.csvFile)
		self.df.to_csv(filename)
		print('Wrote', filename)

		endTime = time.time()
		print('Elapsed %.2fs' % (endTime - startTime))

		return self.df



