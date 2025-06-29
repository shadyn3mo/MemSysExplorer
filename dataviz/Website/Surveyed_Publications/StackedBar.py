# stacked bar plot with filtering by technology

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from ipywidgets import interact, interactive, widgets, HBox, Layout
import ipywidgets as widgets
from IPython.display import display, Markdown
from bokeh.io import output_notebook, show
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, CDSView, BooleanFilter, MultiChoice
from bokeh.layouts import row, column
from bokeh.io import curdoc

from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, show
# from bokeh.palettes import brewer
from bokeh.palettes import viridis
from bokeh.models import HoverTool
import pandas as pd
import os


df = pd.read_csv("../CSV_Files/NVM_data.csv") # CSV filepath
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
           width=1000, height=600)


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

tech_select = MultiChoice(title="Technology:", value=names, options=names)

def update_data(attr, old, new):
    df_temp = df[tech_select.value + ["Year"]]
    source.data = dict(ColumnDataSource(df_temp).data)

tech_select.on_change('value', update_data)

layout = column(tech_select, p)
curdoc().add_root(layout)