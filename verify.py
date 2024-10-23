import sys
import os
import re
import pygraphviz as pgv
from oxidd.bdd import BDDManager
from classes import Operand, OutputAtom, Proposition

def eprint(msg):
    print(msg, file=sys.stderr)

def print_propositions(props):
    print("Merged Propositions:")
    for name, prop in props.items():
        print(f"Name: {name}, Raw String: {prop.raw_string}, Operator: {prop.op}, Inputs: {prop.inputs}")

def resolve_to_oxidd(propositions, name):
    prop = propositions[name]

    if prop.resolved:
        return prop.cached

    if not prop.inputs and prop.op:
        raise Exception(f"inputs is none but operand is: {prop.op}")
    if prop.inputs and not prop.op:
        raise Exception(f"prop has no operand but inputs are: {prop.inputs}")
    if not prop.inputs and not prop.op:
        return prop.oxiddvariable

    resolved_input_variables = [resolve_to_oxidd(propositions, i) for i in prop.inputs]

    prop.cached = prop.op.apply(resolved_input_variables)
    prop.resolved = True
    return prop.cached

def parse_bench_file(file_path, propositions):
    input_atoms = []
    output_atoms = []
    output_counter = 1

    with open(file_path, 'r') as file:
        for line in file:
            # Check if the line is an input line
            if line.startswith("INPUT"):
                # Extract the name between the brackets
                name = re.search(r'\((.*?)\)', line).group(1)
                input_atoms.append(name)
                # Add to propositions with no operation and empty inputs
                propositions[name] = Proposition(name, line.strip())
            # Check if the line is an output line
            elif line.startswith("OUTPUT"):
                # Extract the name between the brackets
                name = re.search(r'\((.*?)\)', line).group(1)
                # Create an OutputAtom instance and add it to the list
                output_atoms.append(OutputAtom(name, output_counter))
                output_counter += 1
                # Add to propositions with no operation and empty inputs
                propositions[name] = Proposition(name, line.strip())
            # Check if the line is an assignment to intermediary wires
            elif '=' in line:
                # Split the line into name and raw string
                name, raw_string = line.split('=', 1)
                name = name.strip()
                raw_string = raw_string.strip()
                # Extract the operator and inputs from the raw string
                op_match = re.match(r'(\w+)\((.*)\)', raw_string)
                if op_match:
                    op = op_match.group(1)
                    inputs = [input.strip() for input in op_match.group(2).split(',')]
                    # Create a Proposition instance and add it to the dictionary
                    propositions[name] = Proposition(name, raw_string, op, inputs)

    return input_atoms, output_atoms

def write_to_files(manager, normal_circuit_dotfile_dest_path, names, pgv, normal_circuit_png_dest_path, output_atoms, output_list_path, opt_output_atoms, opt_output_list_path):
    manager.dump_all_dot_file(normal_circuit_dotfile_dest_path, functions=names, variables=names)
    original_graph = pgv.AGraph(normal_circuit_dotfile_dest_path)
    original_graph.draw(normal_circuit_png_dest_path, prog="dot")
    write_output_atoms_to_file(output_atoms, output_list_path)
    write_output_atoms_to_file(opt_output_atoms, opt_output_list_path)

def write_output_atoms_to_file(output_atoms, file_path):
    with open(file_path, 'w') as file:
        for atom in output_atoms:
            file.write(f"{atom.name}\n")

bench_dir = 'circuit-bench'
circuit_number = 5

def check_circuit(circuit_number):
    circuit_name = f'circuit{circuit_number:02}'
    normal_circuit_source_path = f'{bench_dir}/{circuit_name}.bench'
    opt_circuit_source_path = f'{bench_dir}/{circuit_name}_opt.bench'

    dest_dir = f'{circuit_name}_out'
    os.makedirs(dest_dir, exist_ok=True)

    normal_circuit_dotfile_dest_path = f'{dest_dir}/{circuit_name}.dot'
    opt_circuit_dotfile_dest_path = f'{dest_dir}/{circuit_name}_opt.dot'
    output_list_path = f'{dest_dir}/{circuit_name}_outputs.txt'
    opt_output_list_path = f'{dest_dir}/{circuit_name}_opt_outputs.txt'

    normal_circuit_png_dest_path = f'{dest_dir}/{circuit_name}.png'

# Check if both bench files exist
    if not os.path.exists(normal_circuit_source_path):
        print(f"Error: {normal_circuit_source_path} does not exist.")
    if not os.path.exists(opt_circuit_source_path):
        print(f"Error: {opt_circuit_source_path} does not exist.")

    propositions = {}

    eprint("parsing bench files")

    input_atoms, output_atoms = parse_bench_file(normal_circuit_source_path, propositions)
    opt_input_atoms, opt_output_atoms = parse_bench_file(opt_circuit_source_path, propositions)

# Sanity check for input atoms
    missing_in_normal = set(opt_input_atoms) - set(input_atoms)
    missing_in_opt = set(input_atoms) - set(opt_input_atoms)

    if missing_in_normal:
        eprint(f"Inputs in opt file but not in normal file: {missing_in_normal}")
    if missing_in_opt:
        eprint(f"Inputs in normal file but not in opt file: {missing_in_opt}")

    manager = BDDManager(100_000_000, 100_000_000, 1)
    names = []

    eprint("adding propositions")

# Assign new_var() to merged propositions
    for name, prop in propositions.items():
        var = manager.new_var()
        prop.oxiddvariable = var
        names.append((var, name))

# Resolve output_atoms using merged propositions

    eprint("resolving normal output atoms")
    for atom in output_atoms:
        atom.oxiddvariable = resolve_to_oxidd(propositions, atom.name)
        # Update the names list with the new mapping
        for i, (var, n) in enumerate(names):
            if n == atom.name:
                names[i] = (atom.oxiddvariable, atom.name)
                break
        else:
            names.append((atom.oxiddvariable, atom.name))

# Resolve opt_output_atoms using merged propositions
    eprint("resolving opt output atoms")
    for atom in opt_output_atoms:
        atom.oxiddvariable = resolve_to_oxidd(propositions, atom.name)
        # Update the names list with the new mapping
        for i, (var, n) in enumerate(names):
            if n == atom.name:
                names[i] = (atom.oxiddvariable, atom.name)
                break
        else:
            names.append((atom.oxiddvariable, atom.name))

    eprint("checking if outputs are equal in bdd")
    result = True
    for atom in output_atoms:
        id = atom.index
        for opt_atom in opt_output_atoms:
            if opt_atom.index == id:
                if not atom.oxiddvariable == opt_atom.oxiddvariable:
                    result = False
                    print(f'{atom.name} == {opt_atom.name} <==> {atom.oxiddvariable == opt_atom.oxiddvariable}')
    print(f"RESULT={result}")

can_not_check = [12,14,15,16,17,18,19,20]
can_check = [1,2,3,4,5,6,7,8,9,10,11,13]
for i in can_not_check:
    print(f"Checking circuit {i}")
    check_circuit(i)
