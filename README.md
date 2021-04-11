# aws-price-collator
Collators AWS spot prices, defined duration instances and on-demand prices together for comparison. Uses a combination of the AWS API (requires AWS Key file) and 

# Example
See the example.ipynb notebook for example usage.

# Usage
Basic usage is as follows

Setup inputs.
```python
# Region settings
regionId = 'ap-southeast-2'
subRegion = 'a'
loadCsv = False

# Set key path
apiKeyFilePath = <enter_path_to_key_file>

```

Parse the data.
```python
from parseAndCombinePrices import AllPrices

# Full parse
allPrices = AllPrices(apiKeyFilePath=apiKeyFilePath, csvDir='csvFiles', regionId=regionId, subRegion=subRegion)
allPrices.parseAllPrices(spotPrices=True, definedDurationPrices=True, onDemandPrices=True, nodeTypes=True)
# Load from file
allPrices = AllPrices(apiKeyFilePath=apiKeyFilePath, csvDir='csvFiles', regionId=regionId, subRegion=subRegion)
allPrices.parseAllPrices(spotPrices=False, definedDurationPrices=False, onDemandPrices=False, nodeTypes=False)
# Reparse Spot Prices Only
allPrices = AllPrices(apiKeyFilePath=apiKeyFilePath, csvDir='csvFiles', regionId=regionId, subRegion=subRegion)
allPrices.parseAllPrices(spotPrices=True, definedDurationPrices=False, onDemandPrices=False, nodeTypes=False)
```

Results
```python
import pandas as pd

df = allPrices.getDataframe()

with pd.option_context('display.max_rows', 600):
    display(df)
```

Highlighting
```python
import seaborn as sns

with pd.option_context('display.max_rows', 600):
    cm = sns.light_palette("green", as_cmap=True)
    s = df.style.background_gradient(cmap=cm, subset=['SpotProp%', '1Hr%', '6Hr%'])
    display(s)
```

Filter by group type
```python
with pd.option_context('display.max_rows', 600):
    display(df.loc['Compute Optimized - Current Generation'])
```

Sorting
```python
with pd.option_context('display.max_rows', 600):
    display(df.loc['Compute Optimized - Current Generation'].sort_values(by='SpotProp%', ascending=False))
```


