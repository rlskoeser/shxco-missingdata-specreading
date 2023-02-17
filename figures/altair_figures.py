import glob
import os.path
import altair as alt
import altair_saver
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

driver = webdriver.Chrome(ChromeDriverManager().install())

# pip install altair altair_saver selenium webdriver_manager

# assuming all json files in this directory are altair json
for filename in glob.glob("*.json"):
    print("Processing %s" % filename)
    # use filename without .json to name the exported figure
    basename = os.path.splitext(os.path.basename(filename))[0]
    # skip if already exists
    if os.path.exists("%s.png" % basename):
        print("%s.png already exists, skipping" % basename)
        continue
    with open(filename) as chart_input:
        chart = alt.Chart.from_json(chart_input.read())
        print("Saving as %s.html" % basename)
        chart.save("%s.html" % basename)
        print("Saving as %s.png" % basename)
        chart.save("%s.png" % basename, scale_factor=2.0, webdriver=driver)
