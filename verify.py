import re

class OutputAtom:
    def __init__(self, name, index):
        self.name = name
        self.index = index

class Proposition:
    def __init__(self, name, raw_string, op=None, inputs=None):
        self.name = name
        self.raw_string = raw_string
        self.op = op
        self.inputs = inputs if inputs is not None else []
        self._oxiddvariable = None  # Initialize the property with a default value

    @property
    def oxiddvariable(self):
        return self._oxiddvariable

    @oxiddvariable.setter
    def oxiddvariable(self, value):
        self._oxiddvariable = value


def parse_bench_file(file_path):
    input_names = []
    output_atoms = []
    propositions = {}
    output_counter = 1

    with open(file_path, 'r') as file:
        for line in file:
            # Check if the line is an input line
            if line.startswith("INPUT"):
                # Extract the name between the brackets
                name = re.search(r'\((.*?)\)', line).group(1)
                input_names.append(name)
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

    return input_names, output_atoms, propositions

# Example usage
file_path = 'circuit-bench/circuit02.bench'
input_names, output_atoms, propositions = parse_bench_file(file_path)

print("Input Names:", input_names)
print("Output Atoms:")
for atom in output_atoms:
    print(f"Name: {atom.name}, Index: {atom.index}")

print("Propositions:")
for name, prop in propositions.items():
    print(f"Name: {name}, Raw String: {prop.raw_string}, Operator: {prop.op}, Inputs: {prop.inputs}")

