from transaction import Transaction
from utility_classes import Hashable, Serializable

class TransactionSet(Hashable, Serializable):
    def __init__(self, transactions):
        self.transactions = transactions

    def serialize(self):
        return list(map(lambda item: item.serialize(), self.transactions))

    @classmethod
    def deserialize(kls, tx_set):
        return TransactionSet(list(map(lambda item: Transaction.deserialize(item), tx_set)))

    def calc_hash(self):
        tx_hash = ''
        
        for tx in self.transactions:
            tx_hash = self.hash_str(tx_hash + tx.calc_hash())
            
        return tx_hash