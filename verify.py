import time
import os
import re
import sys
from oxidd.bdd import BDDManager
from classes import OutputAtom, Proposition


def eprint(msg):
    print(msg)
    return
    print(msg, file=sys.stderr)

def print_propositions(props):
    for name, prop in props.items():
        eprint(f"Name: {name}, Raw String: {prop.raw_string}, Operator: {prop.op}, Inputs: {prop.inputs}")

def resolve_to_oxidd(propositions, name, manager):
    prop = propositions[name]

    if prop.oxiddvariable and prop.oxiddvariable.manager == manager:
        return prop.oxiddvariable

    if not prop.inputs and prop.op:
        raise Exception(f"inputs is none but operand is: {prop.op}")
    if prop.inputs and not prop.op:
        raise Exception(f"prop has no operand but inputs are: {prop.inputs}")
    if not prop.inputs and not prop.op:
        prop.oxiddvariable = manager.new_var()
        return prop.oxiddvariable

    resolved_input_variables = [resolve_to_oxidd(propositions, i, manager) for i in prop.inputs]

    prop.oxiddvariable = prop.op.apply(resolved_input_variables)
    return prop.oxiddvariable

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


def check_circuit(circuit_number):
    bench_dir = 'circuit-bench'
    circuit_name = f'circuit{circuit_number:02}'
    normal_circuit_source_path = f'{bench_dir}/{circuit_name}.bench'
    opt_circuit_source_path = f'{bench_dir}/{circuit_name}_opt.bench'

    if not os.path.exists(normal_circuit_source_path):
        raise FileNotFoundError(f"Error: {normal_circuit_source_path} does not exist.")
    if not os.path.exists(opt_circuit_source_path):
        raise FileNotFoundError(f"Error: {opt_circuit_source_path} does not exist.")

    propositions = {}
    input_atoms, output_atoms = parse_bench_file(normal_circuit_source_path, propositions)
    opt_input_atoms, opt_output_atoms = parse_bench_file(opt_circuit_source_path, propositions)

    missing_in_normal = set(opt_input_atoms) - set(input_atoms)
    missing_in_opt = set(input_atoms) - set(opt_input_atoms)

    if missing_in_normal:
        raise ValueError(f"Inputs in opt file but not in normal file: {missing_in_normal}")
    if missing_in_opt:
        raise ValueError(f"Inputs in normal file but not in opt file: {missing_in_opt}")

    if len(output_atoms) != len(opt_output_atoms):
        output_atom_names = {atom.name for atom in output_atoms}
        opt_output_atom_names = {atom.name for atom in opt_output_atoms}
        missing_in_output = opt_output_atom_names - output_atom_names
        missing_in_opt_output = output_atom_names - opt_output_atom_names
        error_message = (
            f"Mismatch in the number of output atoms:\n"
            f"output_atoms: {len(output_atoms)}\n"
            f"opt_output_atoms: {len(opt_output_atoms)}\n"
            f"Missing in output_atoms: {missing_in_output}\n"
            f"Missing in opt_output_atoms: {missing_in_opt_output}"
        )
        raise ValueError(error_message)


    start_time = time.time()
    result = True

    for i, atom in enumerate(output_atoms):
        opt_atom = opt_output_atoms[i]

        manager = BDDManager(10_000_000, 10_000_000, 1)

        current_time = time.time()
        #eprint("{:.6f} seconds - {}".format(current_time - start_time, propositions[atom.name].raw_string))
        atom.oxiddvariable = resolve_to_oxidd(propositions, atom.name, manager)
        start_time = current_time

        current_time = time.time()
        #eprint("{:.6f} seconds - {}".format(current_time - start_time, propositions[opt_atom.name].raw_string))
        opt_atom.oxiddvariable = resolve_to_oxidd(propositions, opt_atom.name, manager)
        start_time = current_time

        if not atom.oxiddvariable == opt_atom.oxiddvariable:
            result = False
            eprint(f'{atom.name} == {opt_atom.name} <==> {atom.oxiddvariable == opt_atom.oxiddvariable}')
            break;

    print(result)


can_check = [1,2,3,4,5,6,7,8,9,10,11,12,13,14]
can_not_check = [15,16,17,18,19,20]
test = [15]
for circuit_id in test:
    print(f"Checking circuit {circuit_id}")
    check_circuit(circuit_id)
