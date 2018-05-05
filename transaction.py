import json

from utility_classes import Hashable, Serializable

class Transaction(Hashable, Serializable):
    def __init__(self, contract_id, data, timestamp):
        self.contract_id = contract_id
        self.data = data
        self.timestamp = timestamp
        
    def execute_contract(self):
        # todo execute the contract script by uploading the data to it and evaluating it
        pass

    def serialize(self):
        return {
            'contract': self.contract_id,
            'data': self.data,
            'timestamp': int(self.timestamp)
        }

    @classmethod
    def deserialize(kls, tx):
        assert isinstance(tx, dict), 'tx should be dict'

        assert 'contract' in tx, 'contract should be in tx'
        assert isinstance(tx['contract'], str), 'contract should be str'
        
        assert 'data' in tx, 'data should be in tx'
        assert isinstance(tx['data'], dict), 'data should be dict'
        # todo: blockchains have their own contract's schema that can be used to verify internal tx data
        
        assert isinstance(tx['timestamp'], int), 'timestamp should be int'

        return Transaction(contract_id=tx['contract'], data=tx['data'], timestamp=tx['timestamp'])

    def calc_hash(self):
        tx_str = str(self.contract_id) + json.dumps(self.data) + str(self.timestamp)
        tx_hash = self.hash_str(tx_str)

        return tx_hash