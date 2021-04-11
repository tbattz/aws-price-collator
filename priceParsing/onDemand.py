import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from priceParsing.baseParser import BaseParser



class OnDemand(BaseParser):
	"""
	Parsers current on-demand prices, or reads existing on-demand prices from csv file.
	"""
	def __init__(self, csvDir='csvFiles', regionId='ap-southeast-2', loadCsv=False):
		"""
		:param csvDir: The directory to read/write csv to/from.
		:param regionId: The region Id name, e.g. 'ap-southeast-2'.
		:param loadCsv: True if to load existing data from csv file.
		"""
		csvFile = 'aws-on-demand-prices-' + regionId + '.csv'
		super().__init__(csvDir=csvDir, csvFile=csvFile)
		self.csvDir = csvDir
		self.csvFile = csvFile
		self.regionId = regionId
		self.loadCsv = loadCsv
		self.pageLink = 'https://aws.amazon.com/ec2/pricing/on-demand/'
		self.stepCount = 11

		self.df = None

		if not self.loadCsv:
			self.parseOnDemandPrices()
		else:
			self.loadFromCsv()


	def printStep(self, stepNum, stepStr):
		"""
		Print the step summary.

		:param stepNum: The number of the current step.
		:param stepStr: The string to print for the step.
		"""
		print("[%i/%i]: %s" % (stepNum, self.stepCount, stepStr))

	def parseOnDemandPrices(self):
		"""
		Parse the on-demand prices using the webpage.

		:return: A dataframe of the current defined on-demand prices.
		"""
		startTime = time.time()
		# Create web page driver
		options = Options()
		options.headless = True
		options.add_argument("--window-size=1920,1200")

		driver = webdriver.Chrome(options=options)
		driver.get(self.pageLink)

		# Click Linux Button
		typeButton = WebDriverWait(driver, 5).until(
			EC.visibility_of_element_located((By.XPATH, ".//div[contains(text(), 'Linux')]")))
		typeButton.click()
		self.printStep(1, "Found OS Selection Button")

		# Get section with only one of these buttons
		singleSection = driver.find_element_by_xpath(".//li[contains(@class, 'lb-tabs-content-item lb-active')]")
		self.printStep(2, "Found Selection Selector")

		# Select Region
		# Wait for dropdown to appear
		WebDriverWait(singleSection, 10).until(
			EC.presence_of_element_located((By.XPATH, ".//ul[contains(@class, 'button lb-dropdown-label')]"))).click()
		# Click region
		singleSection.find_element_by_xpath(".//li[@data-region='ap-southeast-2']").click()
		self.printStep(3, "Selected Region Dropdown")

		# Get Tables
		dataRegion = WebDriverWait(singleSection, 10).until(
			EC.presence_of_element_located((By.XPATH, ".//div[@data-region='%s']" % self.regionId)))
		table = WebDriverWait(dataRegion, 10).until(EC.presence_of_element_located((By.XPATH, ".//table")))
		self.printStep(4, "Found section Tables")

		# Parse Data From Tables
		data = []
		headers = [item.text for item in table.find_element_by_xpath(".//thead").find_elements_by_xpath(".//th")]
		headers[0] = 'InstanceType'
		stepCount = 4
		subTables = table.find_elements_by_xpath(".//tbody")

		for subTable in subTables:
			rows = subTable.find_elements_by_xpath(".//tr")
			for row in rows[1:]:
				# Parse columns
				cols = row.find_elements_by_xpath(".//td")
				nodeType = cols[0].text
				vCPU = int(cols[1].text)
				ecu = cols[2].text
				memory = cols[3].text
				storage = cols[4].text
				perHour = float(cols[5].text.replace("$", "").replace(" per Hour", ""))

				# Store data
				rowData = [nodeType, vCPU, ecu, memory, storage, perHour]
				data.append(rowData)

			stepCount += 1
			self.printStep(stepCount, "Parsed Table %i" % (stepCount - 4))

		# Convert to dataframe
		self.df = pd.DataFrame(data, columns=headers)
		self.df = self.df.set_index(['InstanceType'])
		self.df['Linux/UNIX Usage'] = self.df['Linux/UNIX Usage'].astype(float)

		# Write data to disc
		filename = os.path.join(self.csvDir, self.csvFile)
		self.df.to_csv(filename)
		print('Wrote ', filename)

		endTime = time.time()
		print('Elapsed %.2fs' % (endTime - startTime))

		return self.df



