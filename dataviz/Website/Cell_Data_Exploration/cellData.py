# to run use bokeh serve --show cellData.py
# make sure you install bokeh and then add it to your path variable

import pandas as pd
from bokeh.plotting import figure
from bokeh.models import (ColumnDataSource, HoverTool, MultiChoice, RangeSlider,  Select, ColumnDataSource,
                            HoverTool, LegendItem, Range1d, FactorRange, DataRange1d, Div)
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.palettes import viridis
import math
from copy import deepcopy
import markdown

md_text = """
# General Info

The following visualizations rely on a CSV file with the following columns for filtering:

- **Year**
- **Technology**
- **Conference**
- **Structure**

and the following colums exist for plotting:

- **Ron (ohm)**
- **Roff (ohm)**
- **Read Voltage (V)**
- **Write Voltage (V)**
- **Read Speed (ns)**
- **Write Speed (ns)**
- **Read Energy (pJ)**
- **Write Energy (pJ)**
- **Retention (s)**
- **Enduranve**

CSV files should live in a `CSV_Files` folder within the root directory.  
Example path: `../CSV_Files/NVM_data.csv`

See our tool guide for more on graph manipulation.

---

## Scatter Plot

- **Hover details**  
  User can hover over each data point to observe its DOI.
- **Toggle hover**  
  User may disable the hover tooltip via the toolbar if desired.  
- **Filtering**  
  User may use the multi-select dropdown to filter by available technologies. 
  User may select between different columns for the x and y axes using the dropdown.
  User may filter what the range of X values shown using the slider. 
  This filtering persists for the original X axis when the X axis is changed.
- **Dataset summary**  
  A summary with information about the dataset is displayed alongside the graph.  
- **Missing data**  
  Any rows with relevant missing values are excluded from the visualization.

## Dataset Statistics
"""

html = markdown.markdown(md_text, extensions=['extra'])
comment = Div(
    text=html, 
    width=500, 
    styles={ 
      'font-size': '14px',   
    }
)

#Read in data and ensure it is well formatted
df2 = pd.read_csv("../CSV_Files/NVM_data.csv")
originalRows = len(df2)
df2 = df2.replace(',','', regex=True)
df2 = df2.dropna(subset=['Technology'])
df2['Ron (ohm)'] = df2['Ron (ohm)'].astype('float') 
df2['Roff (ohm)'] = df2['Roff (ohm)'].astype('float') 
df2['Read Voltage (V)'] = df2['Read Voltage (V)'].astype('float') 
df2['Write Voltage (V)'] = df2['Write Voltage (V)'].astype('float') 
df2['Read Speed (ns)'] = df2['Read Speed (ns)'].astype('float') 
df2['Write Speed (ns)'] = df2['Write Speed (ns)'].astype('float') 
df2['Read Energy (pJ)'] = df2['Read Energy (pJ)'].astype('float') 
df2['Write Energy (pJ)'] = df2['Write Energy (pJ)'].astype('float') 
df2['Endurance'] = df2['Endurance'].astype('float') 
df2['Retention (s)'] = df2['Retention (s)'].astype('float') 

#Treating years as strings yields cleaner graphs
df2['Year'] = df2['Year'].astype(str)

# Initial filtered data source (defaulting to 'FeFET' and 'ohm')
initial_tech = 'FeFET'
initial_x = 'ohm'
df2_filtered = df2[df2['Technology'] == initial_tech]
filteredRows = len(df2_filtered)
cds = ColumnDataSource(df2)
filtered_cds = ColumnDataSource(df2_filtered)

# Define possible Y-axis options
x_axis_options = {
    'ohm': ['Ron (ohm)', 'Roff (ohm)'],
    'V': ['Read Voltage (V)', 'Write Voltage (V)'],
    'ns': ['Read Speed (ns)', 'Write Speed (ns)'],
    'pj': ['Read Energy (pJ)', 'Write Energy (pJ)'],
    'Endurance (cycles)': ['Endurance'],
    'Retention (s)': ['Retention (s)']
}

x_axis_ranges = {
    'ohm': (),
    'V': (),
    'ns': (),
    'pj': ()
}

x_axis_list = list(x_axis_options.keys())

#If you need additional technologies, add more markers here
markers = {
    'FeFET': 'circle',
    'RRAM': 'square',
    'STT': 'triangle',
    'PCM': 'hex',
    'FeFET/RRAM': 'diamond',
    'CBRAM': 'inverted_triangle', 
    'FeRAM': 'star'
}

df2['markers'] = df2['Technology'].map(markers)

#To change what is shown when hovering over a data point, simply add to TOOLTIPS
TOOLTIPS = [('DOI', '@{DOI}')]
hvr = HoverTool(tooltips=TOOLTIPS)

# Create figure
fig = figure(
    title=f"Dissagregated technology characteristics",
    background_fill_color="#fafafa",
    x_axis_type="log",
    y_axis_label='Year',
    x_axis_label=initial_x,
    y_range = FactorRange(*sorted(df2['Year'].astype(str).unique())),
    x_range=DataRange1d(), 
    tools="pan,wheel_zoom,box_zoom, save, reset, fullscreen, help",
    width = 800
)

fig.legend.orientation = "vertical"
fig.legend.location = "top_left"
fig.legend.label_text_font_size = "10pt"
fig.xaxis.axis_label_text_font_size = "16pt"
fig.yaxis.axis_label_text_font_size = "16pt"
fig.title.text_font_size = "18pt"
fig.xaxis.major_label_text_font_size = "14pt"
fig.yaxis.major_label_text_font_size = "14pt"
fig.legend.click_policy = "hide"

#Create the legend, going through each technology and adding it
#This code should work even if you add or remove technologies
legend_items = []
for label, marker_type in markers.items():
    if hasattr(fig, marker_type):
        glyph = fig.scatter(marker = marker_type, x=[1], y=[1], size=0)  # Invisible point
        legend_items.append(LegendItem(label=label, renderers=[glyph]))
    else:
        print(f"Warning: marker '{marker_type}' not recognized by Bokeh figure.")

#Add everything to the figure
fig.add_tools(hvr)
fig.scatter(x_axis_options[initial_x][0], 'Year' , source=filtered_cds, color=viridis(2)[0], 
            size=10, legend_label=x_axis_options[initial_x][0])
fig.scatter(x_axis_options[initial_x][1], 'Year', source=filtered_cds, color=viridis(2)[1], 
            size=10, legend_label=x_axis_options[initial_x][1])
fig.legend.items = fig.legend.items + (legend_items)

df_temp = df2_filtered.dropna(subset=x_axis_options[initial_x], thresh=len(x_axis_options[initial_x]))
relevantData = len(df_temp)

#Calculate the range for the figure
#We have to calculate over multiple different columns
mins = [10^30]
maxs = [1]
for x in range(len(x_axis_options[initial_x])):
    mins.append(df2_filtered[x_axis_options[initial_x][x]].dropna().min())
    maxs.append(df2_filtered[x_axis_options[initial_x][x]].dropna().max())
fig.x_range=Range1d(min([x for x in mins if not math.isnan(x)]) / 10, max([x for x in maxs if not math.isnan(x)]) * 10)

#We also want a log scale version to use for filtering
for x in x_axis_list:
    mins = [10^30]
    maxs = [1]
    for y in range(len(x_axis_options[x])):
        mins.append(df2_filtered[x_axis_options[x][y]].dropna().min())
        maxs.append(df2_filtered[x_axis_options[x][y]].dropna().max())
    min1 = min([x for x in mins if not math.isnan(x)])
    max1 = max([x for x in maxs if not math.isnan(x)])
    x_axis_ranges[x] = (math.log10(min1), math.log10(max1))

x_axis_max_ranges = deepcopy(x_axis_ranges)

# Dropdown selectors and range selector
tech_select = MultiChoice(title="Technology:", value=[initial_tech], options=df2['Technology'].unique().tolist())
yaxis_select = Select(title="Y Axis:", value='Year', options=['Year', 'Conference', 'Structure'])
xaxis_select = Select(title="X Axis:", value=initial_x, options=list(x_axis_options.keys()))
slider = RangeSlider(title="X Range (log)", start = x_axis_ranges[initial_x][0], end = x_axis_ranges[initial_x][1], 
                     value = (x_axis_ranges[initial_x][0], x_axis_ranges[initial_x][1]), step=0.0001)

#Called when you change the tech selection or one of the drop downs
def update_data(attr, old, new):
    #Read in values from the interactive features
    selected_techs = tech_select.value
    selected_yaxis = yaxis_select.value
    selected_xaxis = xaxis_select.value
    slider.start = x_axis_max_ranges[selected_xaxis][0]
    slider.end = x_axis_max_ranges[selected_xaxis][1]
    slider.value = (x_axis_ranges[selected_xaxis][0], x_axis_ranges[selected_xaxis][1])

    # Filter data
    new_data = df2[df2['Technology'].isin(selected_techs)]
    for x in x_axis_list:
        for y in range(len(x_axis_options[x])):
            new_data = new_data[(new_data[x_axis_options[x][y]] >= 10 ** x_axis_ranges[x][0]) | (new_data[x_axis_options[x][y]].isna())]
            new_data = new_data[(new_data[x_axis_options[x][y]] <= 10 ** x_axis_ranges[x][1]) | (new_data[x_axis_options[x][y]].isna())]
    # Update data source
    filtered_cds.data = new_data
    
    # Update Y-axis label and remove scatters
    fig.renderers = []
    fig.legend.items = []
    fig.yaxis[0].axis_label = selected_yaxis
    fig.xaxis[0].axis_label = selected_xaxis
    fig.y_range = FactorRange(*sorted(df2[selected_yaxis].astype(str).unique()))
    #Calculate the range
    mins = [10^30]
    maxs = [1]
    for x in range(len(x_axis_options[selected_xaxis])):
        mins.append(new_data[x_axis_options[selected_xaxis][x]].dropna().min())
        maxs.append(new_data[x_axis_options[selected_xaxis][x]].dropna().max())
    fig.x_range=Range1d(min([x for x in mins if not math.isnan(x)]) / 10, max([x for x in maxs if not math.isnan(x)]) * 10)

    # Add new scatters
    for x in range(len(x_axis_options[selected_xaxis])):
        fig.scatter(x_axis_options[selected_xaxis][x], selected_yaxis, source=filtered_cds, color=viridis(len(x_axis_options[selected_xaxis]))[x], 
                    size=10, legend_label=x_axis_options[selected_xaxis][x], marker = 'markers')
    
    #Redo the legend (the legend should always stay the same, but removing the scatters messes it up)
    legend_items = []
    for label, marker_type in markers.items():
        if hasattr(fig, marker_type):
            glyph = fig.scatter(marker = marker_type, x=[1], y=[1], size=0)  # Invisible point
            legend_items.append(LegendItem(label=label, renderers=[glyph]))
        else:
            print(f"Warning: marker '{marker_type}' not recognized by Bokeh figure.")

    fig.legend.items = fig.legend.items + (legend_items)

    #Update missing data description
    filteredRows = len(new_data)
    df_temp = new_data.dropna(subset=x_axis_options[selected_xaxis], thresh=1)
    relevantData = len(df_temp)
    datasetStats.text = f"""
        <div style="margin-left: 30px;">
            <li><b>Original rows in the dataset:</b> {originalRows}</li>
            <li><b>Relevant rows:</b> {filteredRows}</li>
            <li><b>Rows plotted:</b> {relevantData}</li>
            <li><b>Rows dropped due to missing data:</b> {filteredRows - relevantData}</li>
        </div>
        """

#Called when changing the X axis range, very similar to update_data
def update_data2(attr, old, new):

    selected_techs = tech_select.value
    selected_yaxis = yaxis_select.value
    selected_xaxis = xaxis_select.value
    x_axis_ranges[selected_xaxis] = slider.value
    
    # Filter data
    new_data = df2[df2['Technology'].isin(selected_techs)]
    for x in x_axis_list:
        for y in range(len(x_axis_options[x])):
            new_data = new_data[(new_data[x_axis_options[x][y]] >= 10 ** x_axis_ranges[x][0]) | (new_data[x_axis_options[x][y]].isna())]
            new_data = new_data[(new_data[x_axis_options[x][y]] <= 10 ** x_axis_ranges[x][1]) | (new_data[x_axis_options[x][y]].isna())]
    # Update data source
    filtered_cds.data = new_data
    
    # Update Y-axis label and remove scatters
    fig.renderers = []
    fig.legend.items = []
    fig.yaxis[0].axis_label = selected_yaxis
    fig.xaxis[0].axis_label = selected_xaxis
    #Calculate ranges for the figure
    fig.y_range = FactorRange(*sorted(df2[selected_yaxis].astype(str).unique()))
    mins = [10^30]
    maxs = [1]
    for x in range(len(x_axis_options[selected_xaxis])):
        mins.append(new_data[x_axis_options[selected_xaxis][x]].dropna().min())
        maxs.append(new_data[x_axis_options[selected_xaxis][x]].dropna().max())
    fig.x_range=Range1d(min([x for x in mins if not math.isnan(x)]) / 10, max([x for x in maxs if not math.isnan(x)]) * 10)

    # Add new scatters
    for x in range(len(x_axis_options[selected_xaxis])):
        fig.scatter(x_axis_options[selected_xaxis][x], selected_yaxis, source=filtered_cds, color=viridis(len(x_axis_options[selected_xaxis]))[x], 
                    size=10, legend_label=x_axis_options[selected_xaxis][x], marker = 'markers')
    
    #Redo the legend
    legend_items = []
    for label, marker_type in markers.items():
        if hasattr(fig, marker_type):
            glyph = fig.scatter(marker = marker_type, x=[1], y=[1], size=0)  # Invisible point
            legend_items.append(LegendItem(label=label, renderers=[glyph]))
        else:
            print(f"Warning: marker '{marker_type}' not recognized by Bokeh figure.")

    fig.legend.items = fig.legend.items + (legend_items)

    #Update the missing data description
    filteredRows = len(new_data)
    df_temp = new_data.dropna(subset=x_axis_options[selected_xaxis], thresh=1)
    relevantData = len(df_temp)
    datasetStats.text = f"""
        <div style="margin-left: 30px;">
            <li><b>Original rows in the dataset:</b> {originalRows}</li>
            <li><b>Relevant rows:</b> {filteredRows}</li>
            <li><b>Rows plotted:</b> {relevantData}</li>
            <li><b>Rows dropped due to missing data:</b> {filteredRows - relevantData}</li>
        </div>
        """


datasetStats = Div(text=f"""
    <div style="margin-left: 30px;">
        <li><b>Original rows in the dataset:</b> {originalRows}</li>
        <li><b>Relevant rows:</b> {filteredRows}</li>
        <li><b>Rows plotted:</b> {relevantData}</li>
        <li><b>Rows dropped due to missing data:</b> {filteredRows - relevantData}</li>
    </div>
""", 
    width=500, 
    styles={ 
      'font-size': '14px',   
    })

# Attach callback to interactive features
tech_select.on_change('value', update_data)
xaxis_select.on_change('value', update_data)
yaxis_select.on_change('value', update_data)
slider.on_change('value_throttled', update_data2)

# Layout and show
curdoc().add_root(comment)
curdoc().add_root(datasetStats)
layout = row(tech_select, xaxis_select, yaxis_select)
curdoc().add_root(layout)
layout2 = column(row(fig), slider)
curdoc().add_root(layout2)
