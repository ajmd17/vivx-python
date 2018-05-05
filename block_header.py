import json

from utility_classes import Hashable, Serializable

class BlockHeader(Hashable, Serializable):
    def __init__(self, version):
        self.version = version
        #self.block_index = block_index

    def serialize(self):
        return {
            'version': str(self.version)
            #'block_index': self.block_index
        }

    @classmethod
    def deserialize(kls, obj):
        assert isinstance(obj, dict), 'block_header should be dict'

        assert 'version' in obj, 'version should be in block_header'
        assert isinstance(obj['version'], str), 'version should be int'

        #assert 'block_index' in obj, 'block_index should be in block_header'
        #assert isinstance(obj['block_index'], int), 'block_index should be int'

        # TODO parse version string...
        return BlockHeader(obj['version'])

    def calc_hash(self):
        return self.hash_str(json.dumps(self.serialize()))