from utility_classes import Hashable, Serializable

class BlockchainMetadata(Hashable, Serializable):
    def __init__(self, data):
        self.data = data

    def serialize(self):
        return self.data

    def get_attr(self, attr):
        return self.data[attr]

    @classmethod
    def deserialize(kls, obj):
        REQUIRED_FIELDS = ['identifier', 'version', 'owner', 'genesis-timestamp', 'contract-chain-identifier']

        assert isinstance(obj, dict), 'obj should be dict'

        for field in REQUIRED_FIELDS:
            assert field in obj, '"{}" is a required field in blockchain metadata'.format(field)

        assert isinstance(obj['identifier'], str), 'identifier should be str'
        assert isinstance(obj['contract-chain-identifier'], str), 'contract-chain-identifier should be str'
        assert isinstance(obj['version'], str), 'version should be str'
        assert isinstance(obj['owner'], str), 'owner should be str'
        assert isinstance(obj['genesis-timestamp'], int), 'genesis-timestamp should be int'
        assert obj['genesis-timestamp'] <= int(time.time()), 'genesis-timestamp should be <= current time'

        return BlockchainMetadata(obj)
    
    def calc_hash(self):
        pass