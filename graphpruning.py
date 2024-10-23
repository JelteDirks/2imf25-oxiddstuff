import os
import pygraphviz as pgv
from oxidd.bdd import BDDManager

filename = "circuit01"
dotfilename = f"{filename}.dot"
reachabledotfilename = f"{filename}_reachable.dot"
pngfilename = f"{filename}.png"
reachablepngfilename = f"{filename}_reachable.png"

# Create a manager for up to 100,000,000 nodes with an apply cache for
# 1,000,000 entries and 1 worker thread
manager = BDDManager(100_000_000, 1_000_000, 1)


u33 = manager.new_var()
u34 = manager.new_var()
u35 = (u33 & ~u34) | (~u33 & u34)

names = [
    (u33, "u33"),
    (u34, "u34"),
    (u35, "u35"),
]

manager.dump_all_dot_file(dotfilename, functions=names, variables=names)

def get_reachable_subgraph(dot_file, start_label, output_file):
    # Load the graph from the .dot file
    graph = pgv.AGraph(dot_file)

    # Find the node that has the specified label and is a box
    start_node = None
    for node in graph.nodes():
        if graph.get_node(node).attr['label'] == start_label and graph.get_node(node).attr['shape'] == 'box':
            start_node = node
            break

    if start_node is None:
        raise ValueError(f"No node with label '{start_label}' and shape 'box' found.")

    # Perform BFS or DFS to get reachable nodes
    reachable_nodes = set()
    edges_to_keep = []

    def dfs(node):
        if node in reachable_nodes:
            return
        reachable_nodes.add(node)
        for neighbor in graph.successors(node):
            edge = graph.get_edge(node, neighbor)
            edges_to_keep.append((node, neighbor, edge.attr['style'], edge.attr['color'], edge.attr['tooltip']))
            dfs(neighbor)

    # Start DFS from the node with the matching label and shape
    dfs(start_node)

    # Create a subgraph containing only the reachable nodes and edges
    subgraph = pgv.AGraph(strict=True, directed=True)
    for node in reachable_nodes:
        subgraph.add_node(node, label=graph.get_node(node).attr['label'], shape=graph.get_node(node).attr['shape'])
    for edge in edges_to_keep:
        subgraph.add_edge(edge[0], edge[1], style=edge[2], color=edge[3], tooltip=edge[4])

    # Write the subgraph to a new .dot file
    subgraph.write(output_file)

get_reachable_subgraph(dotfilename, 'u35', reachabledotfilename)

original_graph = pgv.AGraph(dotfilename)
original_graph.draw(pngfilename, prog="dot")

reachable_graph = pgv.AGraph(reachabledotfilename)
reachable_graph.draw(reachablepngfilename, prog="dot")
