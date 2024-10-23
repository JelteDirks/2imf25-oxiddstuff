import re
from oxidd.bdd import BDDManager
from enum import Enum

class Operand(Enum):
    OR = 1
    AND = 2
    NOT = 3
    NAND = 4
    NOR = 5
    XOR = 6

    @classmethod
    def from_string(cls, string_value):
        try:
            return cls[string_value.upper()]
        except KeyError:
            raise ValueError(f"'{string_value}' is not a valid Operand")

    def apply(self, *args):
        # If a single list is passed as the first argument, unpack it
        if len(args) == 1 and isinstance(args[0], list):
            args = args[0]

        if not args:
            raise ValueError("At least one argument is required")

        if self == Operand.AND:
            result = args[0]
            for arg in args[1:]:
                result &= arg
            return result
        elif self == Operand.OR:
            result = args[0]
            for arg in args[1:]:
                result |= arg
            return result
        elif self == Operand.NOT:
            if len(args) != 1:
                raise ValueError("NOT operation requires exactly one argument")
            return ~args[0]
        elif self == Operand.NAND:
            result = args[0]
            for arg in args[1:]:
                result &= arg
            return ~result
        elif self == Operand.NOR:
            result = args[0]
            for arg in args[1:]:
                result |= arg
            return ~result
        elif self == Operand.XOR:
            result = args[0]
            for arg in args[1:]:
                result ^= arg
            return result
        else:
            raise ValueError(f"Operation not supported for {self.name}")

class OutputAtom:
    def __init__(self, name, index):
        self.name = name
        self.index = index
        self._oxiddvariable = None  # Initialize the property with a default value

    @property
    def oxiddvariable(self):
        return self._oxiddvariable

    @oxiddvariable.setter
    def oxiddvariable(self, value):
        self._oxiddvariable = value

class Proposition:
    def __init__(self, name, raw_string, op=None, inputs=None):
        self.name = name
        self.raw_string = raw_string
        self.op = Operand.from_string(op) if op else None
        self.inputs = inputs if inputs is not None else []
        self.oxiddvariable = None  # Initialize the property with a default value
        self.resolved = False  # Initialize the resolved property
        self.cached = None  # Initialize the cached property

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

manager = BDDManager(1_000_000, 1_000_000, 1)
names = []

for name, prop in propositions.items():
    var = manager.new_var()
    prop.oxiddvariable = var
    names.append((var, name))

for atom in output_atoms:
    atom.oxiddvariable = resolve_to_oxidd(propositions, atom.name)

print("Input Names:", input_names)
print("Output Atoms:")
for atom in output_atoms:
    print(f"Name: {atom.name}, Index: {atom.index}, Oxiddvariable: {atom.oxiddvariable}")

print("Propositions:")
for name, prop in propositions.items():
    print(f"Name: {name}, Raw String: {prop.raw_string}, Operator: {prop.op}, Inputs: {prop.inputs}, Oxiddvariable: {prop.oxiddvariable}, Resolved: {prop.resolved}")

print("Variable Mapping:")
for var, name in names:
    print(f"Variable: {var}, Name: {name}")

