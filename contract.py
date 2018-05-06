from bytecode import Bytecode
from utility_classes import Hashable

class Contract(Hashable):
    def __init__(self, contract_name, schema, bytecode):
        self.contract_name = contract_name
        self.schema = schema
        self.bytecode = bytecode
        
    def calc_hash(self):
        # calculate hash against the source of the contract
        return self.hash_str(self.contract_name + self.schema.calc_hash() + self.bytecode.calc_hash())