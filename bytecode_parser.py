from bytecode import Bytecode
from instruction import *

class BytecodeParser:
    @classmethod
    def analyze(kls, bytecode):
        errors = []

        for ins in bytecode.instructions:
            if Opcode.is_opcode(ins.opcode):
                if ins.opcode == Opcode.NOOP:
                    continue

                assert ins.opcode in OPERANDS

                operand_set = OPERANDS[ins.opcode]

                if len(operand_set) != len(ins.arguments):
                    errors.append("invalid number of arguments for operand '{}' (expects {}, but got {})".format(ins.opcode, len(operand_set), len(ins.arguments)))
                else:
                    for i in range(0, len(ins.arguments)):
                        arg = ins.arguments[i]
                        counterpart =  operand_set[i]

                        if isinstance(counterpart, list):
                            # if list, allow one of type
                            type_match = None

                            for possible_type in counterpart:
                                if possible_type == ValueType.ANY or possible_type == arg.value_type:
                                    type_match = possible_type
                                    break

                            if type_match is None:
                                errors.append("argument #{} does not match the expected type: expected one of the types: {}; got {}".format(i + 1, ', '.join(list(map(lambda item: str(item), counterpart))), arg.value_type))

                        elif arg.value_type != counterpart and counterpart != ValueType.ANY:
                            errors.append("argument #{} does not match the expected type: expected {}; got {}".format(i + 1, counterpart, arg.value_type))

                        if not isinstance(arg.data, REAL_TYPES[arg.value_type]):
                            errors.append("argument #{} is labeled as type '{}' but holds data of internal type '{}'".format(i + 1, arg.value_type, REAL_TYPES[arg.value_type].__name__))
            else:
                errors.append("'{}' is not a valid opcode".format(ins.opcode))

        return errors