import os
import pygraphviz as pgv
import argparse

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

    # Ensure the directory for the output file exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Write the subgraph to a new .dot file
    subgraph.write(output_file)

def main():
    parser = argparse.ArgumentParser(description="Prune a dotfile and find reachable subgraphs.")
    parser.add_argument("input_dotfile", help="Path to the input dotfile.")
    parser.add_argument("output_file", help="Path to the output file containing names.")
    args = parser.parse_args()

    input_dotfile = args.input_dotfile
    output_file = args.output_file

    # Read names from the output file
    with open(output_file, 'r') as f:
        names = [line.strip() for line in f]

    # Get the directory of the input dotfile
    input_dir = os.path.dirname(input_dotfile)

    original_graph = pgv.AGraph(input_dotfile)
    pngfilename = os.path.join(input_dir, f"{os.path.splitext(os.path.basename(input_dotfile))[0]}.png")
    original_graph.draw(pngfilename, prog="dot")

    for name in names:
        uniquename = os.path.join(input_dir, f"{name}_{os.path.splitext(os.path.basename(input_dotfile))[0]}")
        get_reachable_subgraph(input_dotfile, name, f"{uniquename}.dot")
        reachable_graph = pgv.AGraph(f"{uniquename}.dot")
        reachable_graph.draw(f"{uniquename}.png", prog="dot")

if __name__ == "__main__":
    main()
