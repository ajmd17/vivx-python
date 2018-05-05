# a global representation of a specific object on a blockhain
# uses the syntax organization.namespace.blockchain.contract.blockhash.txhash
# not all items are required, only preceding items
class ObjectIdentifier:
    def __init__(self, organization, namespace, blockchain, contract, blockhash, txhash):
        self.organization = organization
        self.namespace = namespace
        self.blockchain = blockchain
        self.contract = contract
        self.blockhash = blockhash
        self.txhash = txhash

    @classmethod
    def parse(kls, identifier):
        parts = identifier.split('.')
        
        for i in range(0, 6 - len(parts)):
            parts.append(None)

        return ObjectIdentifier(*parts)

    def __eq__(self, other):
        if isinstance(other, str) or isinstance(other, ObjectIdentifier):
            return self.__str__() == other

        return False

    def __str__(self):
        parts = [
            self.organization,
            self.namespace,
            self.blockchain,
            self.contract,
            self.blockhash,
            self.txhash
        ]

        return '.'.join([item for item in parts if item is not None])