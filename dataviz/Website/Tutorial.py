# to run use bokeh serve --show Tutorial.py
# make sure you install bokeh and then add it to your path variable

import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, MultiChoice, RangeSlider,  Select, ColumnDataSource
from bokeh.models import HoverTool, LegendItem, Range1d, FactorRange, DataRange1d, Div
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.palettes import viridis
import math
from copy import deepcopy

#Stacked bar:
df = pd.read_csv("CSV_Files/NVM_data.csv") # CSV filepath
df = df.groupby(by=['Technology', 'Year']).size().reset_index(name='Count')

# stacked
df = df.pivot(index='Year', columns='Technology', values='Count').fillna(0)
df.reset_index(inplace=True) 

names = df.columns[1:].tolist()
source = ColumnDataSource(df)
colors = viridis(len(names))

y_max = df[names].values.sum(axis=1).max()

p = figure(x_range=(df["Year"].min() - 1, df["Year"].max() + 1), y_range=(0, df[names].values.sum(axis=1).max() * 1.1),
           x_axis_label='Year', y_axis_label='Publications',
           title='Publications over Time for Various NVM Technologies',
           tools="pan,wheel_zoom,box_zoom, save, reset, fullscreen, help",
           width=800, height=600)


hover = HoverTool(tooltips=[("Year", "@Year"), ("Publications", "@$name")])
p.add_tools(hover)

# p.vbar_stack(stackers=names, x='Year', width=0.8, color=colors, source=source, legend_label=names)
p.vbar_stack(stackers=names, x='Year', width=0.8, color=colors, source=source, 
             legend_label=names, alpha=0.8)
# p.xaxis.major_label_orientation = 0.8
# legends
p.legend.orientation = "vertical"
p.legend.location = "top_left"
p.legend.label_text_font_size = "10pt"
p.xaxis.axis_label_text_font_size = "16pt"
p.yaxis.axis_label_text_font_size = "16pt"
p.title.text_font_size = "18pt"
p.xaxis.major_label_text_font_size = "14pt"
p.yaxis.major_label_text_font_size = "14pt"
p.legend.click_policy = "hide"



df2 = pd.read_csv("CSV_Files/NVM_data.csv")
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


df2['Year'] = df2['Year'].astype(str)

# Initial filtered data source (defaulting to 'FeFET' and 'ohm')
initial_tech = 'FeFET'
initial_x = 'ohm'
df2_filtered = df2[df2['Technology'] == initial_tech]
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


markers = {
    'FeFET': 'circle',
    'RRAM': 'square',
    'STT': 'triangle',
    'PCM': 'hex',
    'FeFET/RRAM': 'diamond'
}

df2['markers'] = df2['Technology'].map(markers)

TOOLTIPS = [('DOI', '@{DOI}')]
hvr = HoverTool(tooltips=TOOLTIPS)
print(sorted(df2['Year'].astype(str).unique()))
print("")

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

circle = fig.circle(x=1, y=1, size=0)
square = fig.square(x=1, y=1, size=0)
triangle = fig.triangle(x=1, y=1, size=0)
diamond = fig.diamond(x=1, y=1, size=0)
hex = fig.hex(x=1, y=1, size=0)

legend_items = [LegendItem(label="FeFET", renderers=[circle]), LegendItem(label="RRAM", renderers=[square]),
                LegendItem(label="STT", renderers=[triangle]), LegendItem(label="PCM", renderers=[hex]),
                LegendItem(label="FeFET/RRAM", renderers=[diamond])]

fig.add_tools(hvr)
fig.scatter(x_axis_options[initial_x][0], 'Year' , source=filtered_cds, color=viridis(2)[0], 
            size=10, legend_label=x_axis_options[initial_x][0])
fig.scatter(x_axis_options[initial_x][1], 'Year', source=filtered_cds, color=viridis(2)[1], 
            size=10, legend_label=x_axis_options[initial_x][1])
fig.legend.items = fig.legend.items + (legend_items)

mins = [10^30]
maxs = [1]
for x in range(len(x_axis_options[initial_x])):
    mins.append(df2_filtered[x_axis_options[initial_x][x]].dropna().min())
    maxs.append(df2_filtered[x_axis_options[initial_x][x]].dropna().max())
print(mins)
fig.x_range=Range1d(min([x for x in mins if not math.isnan(x)]) / 10, max([x for x in maxs if not math.isnan(x)]) * 10)

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

# Dropdown selectors
tech_select = MultiChoice(title="Technology:", value=[initial_tech], options=df2['Technology'].unique().tolist())
yaxis_select = Select(title="Y Axis:", value='Year', options=['Year', 'Conference', 'Structure'])
xaxis_select = Select(title="X Axis:", value=initial_x, options=list(x_axis_options.keys()))
slider = RangeSlider(title="X Range (log)", start = x_axis_ranges[initial_x][0], end = x_axis_ranges[initial_x][1], 
                     value = (x_axis_ranges[initial_x][0], x_axis_ranges[initial_x][1]), step=0.0001)

def update_data(attr, old, new):
    """ Update ColumnDataSource based on dropdown selection """
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
    print(new_data.head())
    
    # Update Y-axis label and remove scatters
    fig.renderers = []
    fig.legend.items = []
    fig.yaxis[0].axis_label = selected_yaxis
    fig.xaxis[0].axis_label = selected_xaxis
    fig.y_range = FactorRange(*sorted(df2[selected_yaxis].astype(str).unique()))
    mins = [10^30]
    maxs = [1]
    for x in range(len(x_axis_options[selected_xaxis])):
        mins.append(new_data[x_axis_options[selected_xaxis][x]].dropna().min())
        maxs.append(new_data[x_axis_options[selected_xaxis][x]].dropna().max())
    print(mins)
    fig.x_range=Range1d(min([x for x in mins if not math.isnan(x)]) / 10, max([x for x in maxs if not math.isnan(x)]) * 10)

    # Add new scatters
    for x in range(len(x_axis_options[selected_xaxis])):
        fig.scatter(x_axis_options[selected_xaxis][x], selected_yaxis, source=filtered_cds, color=viridis(len(x_axis_options[selected_xaxis]))[x], 
                    size=10, legend_label=x_axis_options[selected_xaxis][x], marker = 'markers')
    
    circle = fig.circle(x=1, y=1, size=0)
    square = fig.square(x=1, y=1, size=0)
    triangle = fig.triangle(x=1, y=1, size=0)
    diamond = fig.diamond(x=1, y=1, size=0)
    hex = fig.hex(x=1, y=1, size=0)

    legend_items = [LegendItem(label="FeFET", renderers=[circle]), LegendItem(label="RRAM", renderers=[square]),
                    LegendItem(label="STT", renderers=[triangle]), LegendItem(label="PCM", renderers=[hex]),
                    LegendItem(label="FeFET/RRAM", renderers=[diamond])]

    fig.legend.items = fig.legend.items + (legend_items)

def update_data2(attr, old, new):
    """ Update ColumnDataSource based on dropdown selection """
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
    
    circle = fig.circle(x=1, y=1, size=0)
    square = fig.square(x=1, y=1, size=0)
    triangle = fig.triangle(x=1, y=1, size=0)
    diamond = fig.diamond(x=1, y=1, size=0)
    hex = fig.hex(x=1, y=1, size=0)

    legend_items = [LegendItem(label="FeFET", renderers=[circle]), LegendItem(label="RRAM", renderers=[square]),
                    LegendItem(label="STT", renderers=[triangle]), LegendItem(label="PCM", renderers=[hex]),
                    LegendItem(label="FeFET/RRAM", renderers=[diamond])]

    fig.legend.items = fig.legend.items + (legend_items)

# Attach callback to dropdowns
tech_select.on_change('value', update_data)
xaxis_select.on_change('value', update_data)
yaxis_select.on_change('value', update_data)
slider.on_change('value_throttled', update_data2)

description1 = Div(text="""
    <h3>   By default bokeh includes the following features on a menu to the right of the plot:</h3>
    <ul>
        <li>Pan: click and drag to move the range of values shown</li>
        <li>Box zoom: select a square to zoom in on</li>
        <li>Wheel zoom: zoom in and out with two fingers</li>
        <li>Save: download an image of the plot in its current state</li>
        <li>Reset: reset any zooms or panning you have done</li>
        <li>Fullscreen: bring the plot to fullscreen</li>
        <li>Hover: turn on or off annotations when hovering</li>
    </ul>
    <h3>   All of our graphs also allow you to hover over elements to gain more information.
                   Here hovering will show you the number of publications in a year for a given technology.
    </h3>
        <p>To add hovering functionality to code:</p>
        <code>
        hover = HoverTool(tooltips=[("Year", "@Year"), ("Publications", "@$name")])<br>
        p.add_tools(hover)
        </code>
                   
""", width=600)

space = Div(text=""" <br><br><br><br><h3> Advanced interactive features: </h3>""")

description2 = Div(text="""
    <h3>Many of our plots allow you to filter which technologies are shown using a multichoice.
                   Simply click the box next to where FeFET is shown and select or deselect any technologies you wish.
                  </h3>
        <p>Sample code: <br> </p>
        <code>
              tech_select = MultiChoice(title="Technology:", value=names, options=names) <br>
              def update_data(attr, old, new): <br>
              &nbsp&nbsp&nbspdf_temp = df[tech_select.value + ["Year"]] <br>
              &nbsp&nbsp&nbspsource.data = dict(ColumnDataSource(df_temp).data) <br>
              tech_select.on_change('value', update_data)  <br><br>   
        </code>
    <h3>Some of our plots even allow you to select the axes used. To change them, simply click the dropdown under X or Y axis
                   and select your preferred axis.</h3>
        <p>The code to add this functionality is more involved, but check out our github for example code!</p>
    <h3>On this graph you can also filter the x values shown. These filters will persist even if you change the axes, 
                   so you can apply multiple filters at once. 
        
                   
""", width=600)

# Layout and show
layoutBar = row(p, description1)
curdoc().add_root(layoutBar)
curdoc().add_root(space)
layout = row(tech_select, xaxis_select, yaxis_select)
curdoc().add_root(layout)
layout2 = column(row(fig, description2), slider)
curdoc().add_root(layout2)

