from enum import Enum

class OutputAtom:
    def __init__(self, name, index):
        self.name = name
        self.index = index
        self.oxiddvariable = None  # Initialize the property with a default value


class Proposition:
    def __init__(self, name, raw_string, op=None, inputs=None):
        self.name = name
        self.raw_string = raw_string
        self.op = Operand.from_string(op) if op else None
        self.inputs = inputs if inputs is not None else []
        self.oxiddvariable = None  # Initialize the property with a default value

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
