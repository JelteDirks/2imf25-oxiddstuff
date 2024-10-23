import os
import re
from oxidd.bdd import BDDManager
from classes import Operand, OutputAtom, Proposition

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

def write_output_atoms_to_file(output_atoms, file_path):
    with open(file_path, 'w') as file:
        for atom in output_atoms:
            file.write(f"{atom.name}\n")

# Example usage
bench_dir = 'circuit-bench'
circuit_number = 2
circuit_name = f'circuit{circuit_number:02}'
normal_circuit_source_path = f'{bench_dir}/{circuit_name}.bench'
opt_circuit_source_path = f'{bench_dir}/{circuit_name}_opt.bench'

dest_dir = f'{circuit_name}_out'
os.makedirs(dest_dir, exist_ok=True)

normal_circuit_dotfile_dest_path = f'{dest_dir}/{circuit_name}.dot'
opt_circuit_dotfile_dest_path = f'{dest_dir}/{circuit_name}_opt.dot'
output_list_path = f'{dest_dir}/{circuit_name}_outputs.txt'

# Check if both bench files exist
if not os.path.exists(normal_circuit_source_path):
    print(f"Error: {normal_circuit_source_path} does not exist.")
if not os.path.exists(opt_circuit_source_path):
    print(f"Error: {opt_circuit_source_path} does not exist.")

propositions = {}

input_atoms, output_atoms = parse_bench_file(normal_circuit_source_path, propositions)
opt_input_atoms, opt_output_atoms = parse_bench_file(opt_circuit_source_path, propositions)

# Sanity check for input atoms
missing_in_normal = set(opt_input_atoms) - set(input_atoms)
missing_in_opt = set(input_atoms) - set(opt_input_atoms)

if missing_in_normal:
    print(f"Inputs in opt file but not in normal file: {missing_in_normal}")
if missing_in_opt:
    print(f"Inputs in normal file but not in opt file: {missing_in_opt}")

manager = BDDManager(1_000_000, 1_000_000, 1)
names = []

# Assign new_var() to merged propositions
for name, prop in propositions.items():
    var = manager.new_var()
    prop.oxiddvariable = var
    names.append((var, name))

# Resolve output_atoms using merged propositions
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
for atom in opt_output_atoms:
    atom.oxiddvariable = resolve_to_oxidd(propositions, atom.name)
    # Update the names list with the new mapping
    for i, (var, n) in enumerate(names):
        if n == atom.name:
            names[i] = (atom.oxiddvariable, atom.name)
            break
    else:
        names.append((atom.oxiddvariable, atom.name))

manager.dump_all_dot_file(normal_circuit_dotfile_dest_path, functions=names, variables=names)
write_output_atoms_to_file(output_atoms, output_list_path)
print_propositions(propositions)
