# **Important Notes**

For this research project, our team was given several research questions, each with its own stipulations on the optimal memory configuration that we needed to discover and visualize. All the data that is used is located in the CSVFiles folder of this project. All of this data was outputed by NVMExplorer and is where a lot of the naming conventions we use in this project are from. 

It is important to note that these research questions are strictly comparing RRAM and SRAM as those were part of the guidelines for this project. The reason for this distinction is that we want our work to be replicated and built upon for future use in the MemSysExplorer project, but in this version of the project, we can only support configurations that only utilize RRAM and SRAM technologies as that is all our data has due to our file output configuration we gave to NVMExplorer. The only one that is has different technologies available is the 2016-2020_EnduranceSummary.csv, so if needed, it may be used for future studies. There are also some hard coded in and specifed aspects that can only work if the data sets being passed in only has RRAM and SRAM technologies. We highlight those specifications in each section with some idea of how to generalize those parts for future replication.

For each question, we have priotized creating visualizations that utilize previous concepts from NVMExplorer using IPYWidgets as well as trying to implement them with the Bokeh library which has proven to have its own benefits built in to each graph that provide more room for user interaction. In Bokeh graphs, you will see a list of buttons that toggle on specific actions that users can do to Bokeh graphs. For the sake of clairty, here is the documentation for those toggles:

https://docs.bokeh.org/en/latest/docs/user_guide/interaction/tools.html#ug-interaction-tools

# **Brief Overview**
Below, we've outlined our three guiding research questions, which are labled as "application", "system", or "technology" based on which level of the memory stack these questions seek to optimize performance.

## **Guiding Research Questions**

*   **Application question** (*Speed is the priority*): What configuration should I use for my BFS kernel?  For similar BW requirements (reads/writes per second), what other configs might I consider?

*  **System Question** (*Efficiency is priority*): When should I consider “switching” to RRAM?

*  **Technology Questions** (*Reliability/Lifetime is the priority*): Identify “killer use case” for my technology (RRAM), Identify what the key limitations are of RRAM.

__________
With these questions in mind, we first gathered the necessary data by running NVMExplorer on the following configuration:

As previously stated, for the cell type, we chose to run NVM simulations on RRAM and SRAM cells. At the application and systems level, we care most about speed and efficiency. Thus, we chose to run simulations for the following optimizations: ReadEDP, ReadLatency, ReadDynamicEnergy, Area.
_____

## **Optimization Targets**

**ReadEDP**: Read energy delay product quantifies the trade-off between energy consumption and latency. Ideally, our memory cell would have low energy consumption and faster access times, however there is a tradeoff between energy and delay. A high EDP indicates that the memory technology has a poor trade-off between energy consumption and delay, ie. it requires high energy consumption for any given speed. 
**Note:** that a low ReadEDP is what we would hope to see in an efficient system, thus it is relevant to the Systems question.

**Read Latency**: This is exactly what it sounds like, read latency quantifies the time it takes for a memory system to retrieve data after a read request is made. Low read latency = faster reads.

**Read Dynamic Energy**: How much energy is consumed per read request.

**Area**: How much area on the chip each memory cell takes up.

The traffic patterns we supplied describe different classes of benchmarks to test our configuration on- eg each benchmark is a simulation with a specific ratio of reads/writes, which will allow us to see which traffic patterns, and therefore which applications, our cell performs best at and worst at.

## **Configuration**

Here is our configuration input we used to produce the data for this project

### Written in A .Json File
{"experiment": {
    "exp_name":"S-RRAM_all_opt",  
    "cell_type":["RRAM", "SRAM"],
    "opt_target":["ReadEDP", "ReadLatency", "ReadDynamicEnergy", "Area"],
    "capacity":[1, 2, 4, 8, 16],
    "traffic":["generic", "graph", "spec"],
    "nvsim_path":"./nvmexplorer_src/nvsim_src/nvsim",
    "output_path":"./output"
}
} 

Now, you may take a look at each notebook for the specified research question. At the beginning of every notebook, we make sure to import the libraries important to that section as well as important the data sets from the CSVFiles.

## What to Takeaway
We hope this demonstrates the variety of user interface that Bokeh and IPYWidgets allows for Data Visualization. We awknowledge there are some areas to improve on visualization like general UI, graph optimization, etc, but we have only shown you the relative standards of the libraries and there is more to be explored with them. 
