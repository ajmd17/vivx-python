from utility_classes import Hashable

class ContractSchema(Hashable):
    def __init__(self, fields):
        self.fields = fields
        
    def calc_hash(self):
        raise NotImplementedError()