# FPGA_BOOKSHELF_TOOL
A Python Script for anilising and comparing Bookshelf format FPGA designs

"bookshelf_analyzer.py" gives you stats on a bookshelf format FPGA design, it reports things like utilisation %
number of nodes, nets ect...

"scl_visualizer.py" generates a .png image from a .scl file to visualise the architecture of the FPGA (note this is a bit slow on any actual FPGA)

"fixed_elements_visualizer.py" generates a .png image from .scl and .pl files showing the locations of fixed instances.

* benchmarks from: https://fpga.socs.uoguelph.ca/benchmarks and ispd2016