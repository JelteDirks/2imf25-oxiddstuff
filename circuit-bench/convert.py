import networkx as nx
import pygraphviz as pgv
import os
import re

def parse_iscas_bench(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    gates = []
    for line in lines:
        line = line.strip()
        if line.startswith('#') or not line:
            continue
        if line.startswith('INPUT') or line.startswith('OUTPUT'):
            parts = re.findall(r'\((.*?)\)', line)
            gates.append([line.split('(')[0], parts[0]])
        else:
            match = re.match(r'(\w+)\s*=\s*(\w+)\((.*?)\)', line)
            if match:
                var_name = match.group(1)
                gate_type = match.group(2)
                inputs = match.group(3).split(', ')
                gates.append([var_name, gate_type] + inputs)
    return gates

def create_graph(gates):
    G = nx.DiGraph()
    for gate in gates:
        if gate[0] == 'INPUT':
            G.add_node(gate[1], type='input', label=gate[1], shape='circle', color='green')
        elif gate[0] == 'OUTPUT':
            G.add_node(gate[1], type='output', label=gate[1], shape='circle', color='red')
        else:
            shape = 'box'
            if gate[1] == 'AND':
                shape = 'and'
            elif gate[1] == 'OR':
                shape = 'or'
            elif gate[1] == 'NAND':
                shape = 'invhouse'
            elif gate[1] == 'NOR':
                shape = 'invtrapezium'
            elif gate[1] == 'NOT':
                shape = 'triangle'
            G.add_node(gate[0], type='gate', gate_type=gate[1], label=f"{gate[0]} ({gate[1]})", shape=shape)
            for input_node in gate[2:]:
                G.add_edge(input_node, gate[0])
    return G

def export_to_dot(graph, output_file):
    A = nx.nx_agraph.to_agraph(graph)
    A.write(output_file)

def convert_dot_to_png(dot_file, png_file):
    graph = pgv.AGraph(dot_file)
    graph.draw(png_file, prog="dot")

# Hardcoded example
file = 'circuit02_opt'
iscas_file = f'{file}.bench'
dot_file = f'{file}.dot'
png_file = f'{file}.png'

gates = parse_iscas_bench(iscas_file)
graph = create_graph(gates)
export_to_dot(graph, dot_file)
convert_dot_to_png(dot_file, png_file)

# Remove the DOT file after creating the PNG file
os.remove(dot_file)

print(f"DOT file has been created and converted to PNG: {png_file}")
