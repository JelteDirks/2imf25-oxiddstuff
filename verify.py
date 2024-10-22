import os
import pygraphviz as pgv
from oxidd.bdd import BDDManager

filename = "circuit01"
dotfilename = f"{filename}.dot"
pngfilename = f"{filename}.png"

# Create a manager for up to 100,000,000 nodes with an apply cache for
# 1,000,000 entries and 1 worker thread
manager = BDDManager(100_000_000, 1_000_000, 1)


u33 = manager.new_var()
u34 = ~u33

names = [
    (u33, "u33"),
    (u34, "u34")
]

manager.dump_all_dot_file(dotfilename, variables=names)
graph = pgv.AGraph(dotfilename)
graph.draw(pngfilename, prog="dot")

os.remove(dotfilename)

