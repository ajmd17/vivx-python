from bytecode import Bytecode
from instruction import *

MAX_STACK_SIZE = 64

class VM:
    def __init__(self, bytecode):
        self.bytecode = bytecode
        self.stack = []

    def _ensure_stack_size(self, value):
        assert len(self.stack) >= value, "stack underflow"

    def _math_operation(self):
        self._ensure_stack_size(2)

        a = self.stack[-1]
        self.stack.pop()
        b = self.stack[-1]
        self.stack.pop()

        assert a.value_type == ValueType.INT or a.value_type == ValueType.FLOAT, "value must be a numeric type"
        assert b.value_type == ValueType.INT or b.value_type == ValueType.FLOAT, "value must be a numeric type"

        return (a, b)

    def evaluate(self):
        for ins in self.bytecode.instructions:
            if ins.opcode == Opcode.NOOP:
                pass
            elif ins.opcode == Opcode.PUSH:
                assert len(self.stack) < MAX_STACK_SIZE, "stack overflow"
                value = ins.arguments[0]
                self.stack.append(value)
            elif ins.opcode == Opcode.POP:
                self._ensure_stack_size(1)
                self.stack.pop()
            elif ins.opcode == Opcode.ADD:
                a, b = self._math_operation()
                self.stack.append(Value.create(a.data + b.data))
            elif ins.opcode == Opcode.SUB:
                a, b = self._math_operation()
                self.stack.append(Value.create(a.data - b.data))
            elif ins.opcode == Opcode.MUL:
                a, b = self._math_operation()
                self.stack.append(Value.create(a.data * b.data))
            elif ins.opcode == Opcode.DIV:
                a, b = self._math_operation()
                self.stack.append(Value.create(a.data / b.data))
            elif ins.opcode == Opcode.MOD:
                a, b = self._math_operation()
                self.stack.append(Value.create(a.data % b.data))