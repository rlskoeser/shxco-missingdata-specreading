import glob
import os.path
import altair as alt
import altair_saver

# pip install altair altair_saver selenium

# assuming all json files in this directory are altair json
for filename in glob.glob("*.json"):
    print("Processing %s" % filename)
    # use filename without .json to name the exported figure
    basename = os.path.splitext(os.path.basename(filename))[0]
    with open(filename) as chart_input:
        chart = alt.Chart.from_json(chart_input.read())
        print("Saving as %s.html" % basename)
        chart.save("%s.html" % basename)
        print("Saving as %s.png" % basename)
        chart.save("%s.png" % basename, scale_factor=2.0)
