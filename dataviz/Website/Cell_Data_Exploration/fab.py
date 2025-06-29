#to run
#bokeh serve --show fab2.py
# make sure you install bokeh and then add it to your path variable

###Plots 2 graphs in one page: violin plot on the left and box plot on the right
#The violin plot shows the distribution of process node sizes for each technology, while the box plot shows the summary statistics (min, max, quartiles) for each technology.
#graph assumes that there is a column called "Process Node (nm)" and a column called "Technology" in the data

from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import (ColumnDataSource, FactorRange, HoverTool, Whisker, 
                          MultiChoice, Range1d, Div)
from bokeh.plotting import figure
from bokeh.palettes import Viridis256
from bokeh.transform import factor_cmap
import pandas as pd
import numpy as np
from scipy.stats import gaussian_kde
import markdown


md_text = """
# General Info

The following visualizations show the distribution of process node sizes for each technology, as well as the summary statistics (min, max, quartiles) for each technology. Assumed column names are:

- **Process Node (nm)**
- **Technology**
- **Year**
- **Conference**

CSV files should live in a `CSV_Files` folder within the root directory.  
Example path: `../CSV_Files/NVM_data.csv`

See our tool guide for more on graph manipulation.

---

## Violin and Box Plots For Process Node Size by Technology

- **Hover details**  
  User can hover over each data point to observe its technology type, process node value, and conference.
  User can hover over the violin plot to observe the mean, min, max, and count of process node sizes for each technology.
  User can hover over the box plot to observe the quartiles, min, max, and count of process node sizes for each technology.
- **Toggle hover**  
  User may disable the hover tooltip via the toolbar if desired.  
- **Filtering**  
  User may use the multi-select dropdown to filter by available technologies
- **Dataset summary**  
  A summary with information about the dataset is displayed alongside the graph.  
- **Missing data**  
  Any rows with missing values are excluded from the visualization.
"""

html = markdown.markdown(md_text, extensions=['extra'])
comment = Div(
    text=html, 
    width=500, 
    styles={ 
      'font-size': '14px',   
    }
)


#read data
df = pd.read_csv('../CSV_Files/NVM_data.csv')
initial_count = len(df)

x_axis = 'Process Node (nm)'
y_axis = 'Technology'
conf = 'Conference'
year = 'Year'
#change the file names in CSV_Files to your own as needed


df[x_axis] = pd.to_numeric(df[x_axis], errors="coerce")
df = df.dropna(subset=[y_axis, x_axis])
df = df[~df[x_axis].isin([np.inf, -np.inf])]

final_count = len(df)

stats_md = f"""
## Dataset Statistics

- **Total rows in original dataset:** {initial_count}
- **Rows shown in visualization:** {final_count}
- **Percentage of data shown:** {(final_count/initial_count)*100:.1f}%
- **Rows removed:** {initial_count - final_count} (due to missing or invalid values)

---
"""

#combine the markdown texts
combined_md = md_text + "\n" + stats_md

#update the comment div
html = markdown.markdown(combined_md, extensions=['extra'])
comment = Div(
    text=html, 
    width=500, 
    styles={ 
      'font-size': '14px',   
    }
)

#group by technology for violin plot
tech_groups = df.groupby(y_axis)[x_axis]
tech_list = sorted(tech_groups.groups.keys())

#compute percentiles for box plot
box_tech_groups = df.groupby(y_axis)[x_axis]
box_stats = box_tech_groups.describe()[["25%", "50%", "75%", "min", "max"]]

#color mapping
n_colors = min(len(tech_list), 10)
step = max(1, len(Viridis256) // len(tech_list))
colors = [Viridis256[i * step] for i in range(len(tech_list))]
color_map = {tech: colors[i % len(colors)] for i, tech in enumerate(tech_list)}

#numeric mapping for x-axis in violin plot
x_numeric = {tech: i for i, tech in enumerate(tech_list)}

def to_power_of_10(x):
    """Convert x to a power of 10 for box plot y-axis"""
    return 10 ** np.floor(np.log10(x))

#violin plot
def create_violin_plot():
    # figure for violin plot
    pv = figure(
        y_axis_label=x_axis + " Size", 
        # tools="pan,box_zoom,reset,save",  
        title=x_axis+" Size Distribution by "+y_axis,
        x_range=Range1d(-0.5, len(tech_list) - 0.5)
    )

    pv.legend.label_text_font_size = "10pt"
    pv.legend.orientation = "vertical"
    pv.legend.location = "top_left"
    pv.xaxis.axis_label_text_font_size = "16pt"
    pv.yaxis.axis_label_text_font_size = "16pt"
    pv.title.text_font_size = "18pt"
    pv.xaxis.major_label_text_font_size = "14pt"
    pv.yaxis.major_label_text_font_size = "14pt"
    pv.title.align = "left"

    #sources for filtering
    violin_sources = {}
    scatter_sources = {}

    for tech in tech_list:
        data = tech_groups.get_group(tech).dropna()
        data = data[np.isfinite(data)]
        
        if len(data) > 1:
            #stats
            mean_val = data.mean()
            min_val = data.min()
            max_val = data.max()
            count = len(data)
            
            #calculate KDE on linear scale
            kde = gaussian_kde(data, bw_method=0.3)  # Linear scale
            x_vals = np.linspace(data.min(), data.max(), 100)
            y_vals = kde(x_vals)
            y_vals /= y_vals.max()  #normalize
            y_vals *= 0.4  #change width
            
            #patch coordinates
            x_patch = np.concatenate([x_vals, x_vals[::-1]])
            y_patch = np.concatenate([np.full_like(y_vals, x_numeric[tech] - y_vals), 
                                      np.full_like(y_vals, x_numeric[tech] + y_vals[::-1])])
            
            #source
            violin_source = ColumnDataSource(data={
                'x': y_patch, 
                'y': x_patch,
                'tech': [tech] * len(x_patch),
                'fab': [None] * len(x_patch)
            })
            #dictionary for tech
            violin_sources[tech] = violin_source
            
            #renderer
            violin_renderer = pv.patch(
                'x', 'y', source=violin_source, 
                alpha=0.7, 
                fill_color=color_map[tech], 
                line_color="black"
            )
            
            hover = HoverTool(
                tooltips=[
                    (y_axis, tech),
                    ("Mean", f"{mean_val:.2f}"),
                    ("Min", f"{min_val}"),
                    ("Max", f"{max_val}"),
                    ("Count", str(count))
                ],
                renderers=[violin_renderer],
                visible=False
            )
            pv.add_tools(hover)

        #scatter
        tech_data = df[df[y_axis] == tech].copy()
        tech_data['x_pos'] = x_numeric[tech]
        
        scatter_source = ColumnDataSource(tech_data)
        scatter_sources[tech] = scatter_source
        
        scatter_renderer = pv.scatter(
            x='x_pos', 
            y=x_axis, 
            source=scatter_source, 
            size=6, color='black', 
            alpha=0.5
            )
        
        scatter_hover = HoverTool(
            tooltips=[
                (y_axis, "@"+y_axis),
                (x_axis, "@{"+x_axis+"}"),
                (conf, "@"+conf),
                (year, "@"+year) 
            ],
            renderers=[scatter_renderer],
            visible=False
        )
        pv.add_tools(scatter_hover)

    #setx-axis
    pv.xaxis.ticker = [x_numeric[tech] for tech in tech_list]
    pv.xaxis.major_label_overrides = {x_numeric[tech]: tech for tech in tech_list}

    return pv, violin_sources, scatter_sources

#box plot
def create_box_plot():
    pb = figure(
        x_range=FactorRange(*box_stats.index),
        title=x_axis+" Size by "+y_axis,
        y_axis_label=x_axis,
        # tools="pan,box_zoom,reset,save",
        background_fill_color="#efefef",
    )

    pb.legend.label_text_font_size = "10pt"
    pb.legend.orientation = "vertical"
    pb.legend.location = "top_left"
    pb.xaxis.axis_label_text_font_size = "16pt"
    pb.yaxis.axis_label_text_font_size = "16pt"
    pb.title.text_font_size = "18pt"
    pb.xaxis.major_label_text_font_size = "14pt"
    pb.yaxis.major_label_text_font_size = "14pt"
    pb.title.align = "left"

    pb.y_range.start = 0.5 * df[x_axis].min()
    pb.y_range.end = 1.1 * df[x_axis].max()

    counts = box_tech_groups.count().tolist()
    box_source = ColumnDataSource(data={
        "tech": box_stats.index.tolist(),
        "q1": box_stats["25%"].tolist(),
        "q2": box_stats["50%"].tolist(),
        "q3": box_stats["75%"].tolist(),
        "lower": box_stats["min"].tolist(),
        "upper": box_stats["max"].tolist(),
        "count": counts
    })

    scatter_source = ColumnDataSource(df)

    box = pb.vbar(x="tech", top="q3", bottom="q1", width=0.6, source=box_source,
                 fill_color=factor_cmap("tech", palette=colors, factors=box_stats.index),
                 line_color="black",
                 alpha=0.7)

    whisker = Whisker(base="tech", upper="upper", lower="lower", source=box_source)
    pb.add_layout(whisker)

    #scatter
    dots = pb.scatter(
        x=y_axis, 
        y=x_axis, 
        source=scatter_source, 
        size=6, 
        color="black", 
        alpha=0.5)

    pb.add_tools(HoverTool(
        tooltips=[
            (y_axis, "@tech"), 
            ("25th Percentile", "@q1"),
            ("Median", "@q2{0.00}"), 
            ("75th Percentile", "@q3"),
            ("Min", "@lower"), 
            ("Max", "@upper"),
            ("Count", "@count")
        ],
        renderers=[box],
        visible=False
    ))
    pb.add_tools(HoverTool(
        tooltips=[
            (y_axis, "@"+y_axis), 
            (x_axis, "@{"+x_axis+"}"),
            (conf, "@"+conf),
            (year, "@"+year) 
        ],
        renderers=[dots],
        visible=False
    ))

    return pb, box_source, scatter_source

#make plots
violin_plot, violin_sources, scatter_violin_sources = create_violin_plot()
box_plot, box_source, scatter_box_source = create_box_plot()

#filtering
checkbox = MultiChoice(title= y_axis+":", options=tech_list, value=tech_list)

def update_plot(attr, old, new):
    global violin_plot, box_plot, violin_sources, scatter_violin_sources, box_source, scatter_box_source

    selected_techs = [tech for tech in tech_list if tech in checkbox.value]
    
    #if no technologies selected, use all
    if not selected_techs:
        selected_techs = tech_list

    #filter data for all plots
    filtered_df = df[df[y_axis].isin(selected_techs)]

    #recalculate x_numeric for selected technologies
    selected_x_numeric = {tech: i for i, tech in enumerate(selected_techs)}

    #prepare violin plot data
    for tech in tech_list:  #iterate through ALL technologies
        if tech in selected_techs:
            tech_data = filtered_df[filtered_df[y_axis] == tech][x_axis]
            
            tech_data = tech_data[np.isfinite(tech_data)]
            
            if len(tech_data) > 1:
                try:
                    kde = gaussian_kde(tech_data, bw_method=0.3)
                    x_vals = np.linspace(tech_data.min(), tech_data.max(), 100)
                    y_vals = kde(x_vals)
                    y_vals /= y_vals.max()
                    y_vals *= 0.4

                    x_patch = np.concatenate([x_vals, x_vals[::-1]])
                    y_patch = np.concatenate([
                        np.full_like(y_vals, selected_x_numeric[tech] - y_vals), 
                        np.full_like(y_vals, selected_x_numeric[tech] + y_vals[::-1])
                    ])

                    #update violin source
                    if tech in violin_sources:
                        violin_sources[tech].data = {
                            'x': y_patch, 
                            'y': x_patch,
                            'tech': [tech] * len(x_patch),
                            'pn': [None] * len(x_patch)
                        }

                    #update scatter source
                    if tech in scatter_violin_sources:
                        tech_scatter_data = filtered_df[filtered_df[y_axis] == tech].copy()
                        tech_scatter_data['x_pos'] = selected_x_numeric[tech]
                        
                        scatter_violin_sources[tech].data = tech_scatter_data.to_dict(orient='list')
                
                except Exception as e:
                    print(f"Error processing {tech}: {e}")
                    #clear sources on error
                    if tech in violin_sources:
                        violin_sources[tech].data = {'x': [], 'y': [], 'tech': [], 'pn': []}
                    if tech in scatter_violin_sources:
                        scatter_violin_sources[tech].data = {
                            'x_pos': [], x_axis: [], y_axis: []
                        }
            else:
                #not enough data points, clear sources
                if tech in violin_sources:
                    violin_sources[tech].data = {'x': [], 'y': [], 'tech': [], 'pn': []}
                if tech in scatter_violin_sources:
                    scatter_violin_sources[tech].data = {
                        'x_pos': [], x_axis: [], y_axis: []
                    }
        else:
            #technology is not selected, clear sources
            if tech in violin_sources:
                violin_sources[tech].data = {'x': [], 'y': [], 'tech': [], 'pn': []}
            if tech in scatter_violin_sources:
                scatter_violin_sources[tech].data = {
                    'x_pos': [], x_axis: [], y_axis: []
                }

    #update x-axis labels and range for violin plot
    violin_plot.x_range.start = -0.5
    violin_plot.x_range.end = len(selected_techs) - 0.5
    violin_plot.xaxis.ticker = [selected_x_numeric[tech] for tech in selected_techs]
    violin_plot.xaxis.major_label_overrides = {selected_x_numeric[tech]: tech for tech in selected_techs}

    #update box plot 
    if len(filtered_df) > 0:
        filtered_stats = filtered_df.groupby(y_axis)[x_axis].describe()[["25%", "50%", "75%", "min", "max"]]
        filtered_counts = filtered_df.groupby(y_axis)[x_axis].count()
        
        box_source.data = {
            "tech": filtered_stats.index.tolist(),
            "q1": filtered_stats["25%"].tolist(),
            "q2": filtered_stats["50%"].tolist(),
            "q3": filtered_stats["75%"].tolist(),
            "lower": filtered_stats["min"].tolist(),
            "upper": filtered_stats["max"].tolist(),
            "count": filtered_counts.tolist()
        }
        
        scatter_box_source.data = ColumnDataSource.from_df(filtered_df)

        #update x-axis
        box_plot.x_range.factors = filtered_stats.index.tolist()
    else:
        #if no data is selected, clear sources
        box_source.data = {
            "tech": [], "q1": [], "q2": [], "q3": [], 
            "lower": [], "upper": []
        }
        scatter_box_source.data = ColumnDataSource(data=pd.DataFrame())

#attach callback to checkbox
checkbox.on_change('value', update_plot)

layout = column(
    comment,
    row(checkbox),
    row(violin_plot, box_plot)
)

#show
curdoc().add_root(layout)
curdoc().title = x_axis+" Visualization"
