import hashlib

class Serializable:
    def serialize(self):
      raise NotImplementedError()

    @classmethod
    def deserialize(kls, obj):
        raise NotImplementedError()

class Identifiable:
    def get_identifier(self):
        raise NotImplementedError()

class Hashable:
    def hash_str(self, data):
        return hashlib.sha256(str(data).encode('utf-8')).hexdigest()

    def calc_hash(self):
        raise NotImplementedError()