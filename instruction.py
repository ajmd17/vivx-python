from enum import Enum

from utility_classes import Hashable

class Opcode(Enum):
    NOOP = 0
    LOAD = 1 # loads a PTR at address
    PUSH = 2
    POP = 3
    ADD = 4
    SUB = 5
    MUL = 6
    DIV = 7
    MOD = 8

    @classmethod
    def is_opcode(kls, value):
        if isinstance(value, kls):
            return any(value.value == item.value for item in kls)
        else:
            return any(value == item.value for item in kls)

class ValueType(Enum):
    ANY = 0
    PTR = 1
    INT = 2
    FLOAT = 3
    STRING = 4
    BOOL = 5
    ARRAY = 6
    DICT = 7

REAL_TYPES = {
    ValueType.PTR: int,
    ValueType.INT: int,
    ValueType.FLOAT: float,
    ValueType.STRING: str,
    ValueType.BOOL: bool,
    ValueType.ARRAY: list,
    ValueType.DICT: dict
}

OPERANDS = {
    Opcode.LOAD: [ValueType.PTR],
    Opcode.PUSH: [ValueType.ANY],
    Opcode.POP: [],
    Opcode.ADD: [],
    Opcode.SUB: [],
    Opcode.MUL: [],
    Opcode.DIV: [],
    Opcode.MOD: [],
}

class Value(Hashable):
    def __init__(self, value_type, data):
        self.value_type = value_type
        self.data = data
        
    @classmethod
    def create(kls, data):
        for key, value in REAL_TYPES.items():
            if isinstance(data, value):
                return kls(key, data)

        raise Exception("no compatible type known for {}".format(type(data).__name__))

    def calc_hash(self):
        return self.hash_str(self.hash_str(self.value_type) + self.hash_str(self.data))

class Instruction(Hashable):
    def __init__(self, opcode, arguments=[]):
        self.opcode = opcode
        self.arguments = arguments

    def calc_hash(self):
        arg_hash = ''

        for arg in self.arguments:
            arg_hash = self.hash_str(arg_hash + arg.calc_hash())

        return self.hash_str(self.opcode.calc_hash() + arg_hash)