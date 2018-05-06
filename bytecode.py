from utility_classes import Hashable

class Bytecode(Hashable):
    def __init__(self, instructions):
        self.instructions = instructions

    def calc_hash(self):
        hash_result = ''
        
        for instruction in self.instructions:
            hash_result = self.hash_str(hash_result + instruction.calc_hash())

        return hash_result