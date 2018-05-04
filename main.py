import time
import hashlib
import json
import os
import re

"""
Example contract file:

{
  sender: {
    type: Address,
    required: true
  },
  recipient: {
    type: Address,
    required: true
  },
  data: {
    value: {
      type: uint64,
      satisfy: [
        "BALANCE(sender) >= VALUE"
      ],
      outcome: [
        "ADD_BALANCE(receiver, VALUE)",
        "SUBTRACT_BALANCE(sender, VALUE)"
      ]
    }
  },
  
}

"""

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

class Identifiable:
    def get_identifier(self):
        raise NotImplementedError()

class Hashable:
    def hash_str(self, data):
        return hashlib.sha256(str(data).encode('utf-8')).hexdigest()

    def calc_hash(self):
        raise NotImplementedError()
    
class ContractSchema(Hashable):
    def __init__(self, fields):
        self.fields = fields
        
    def calc_hash(self):
        raise NotImplementedError()

class Contract(Hashable):
    def __init__(self, contract_name, schema):
        self.contract_name = contract_name
        self.schema = schema
        
    def calc_hash(self):
        # calculate hash against the source of the contract
        return self.hash_str(self.contract_name + self.schema.calc_hash())


class Serializable:
  def serialize(self):
    raise NotImplementedError()

  @classmethod
  def deserialize(kls, obj):
    raise NotImplementedError()


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

class Blockchain(Identifiable):
    def __init__(self, genesis_block, last_block, metadata):
        self.contracts = {}
        self.genesis_block = genesis_block
        self.last_block = last_block
        self.metadata = metadata
    """
    def add_contract(contract):
        assert isinstance(contract, Contract)
        
        contract_hash = contract.calc_hash()
        
        assert contract_hash not in self.contracts, "contract already added"
        self.contracts[contract_hash] = contract
        
        # TODO: upload the contract to the "CORE" contract chain (a subchain of the meta-chain)
    """
    def get_identifier(self):
        return ObjectIdentifier.parse(self.metadata.get_attr('identifier'))

    def load_blocks(self):
        # attempt to load blocks from the 'chains/<identifier>/blocks' folder
        identifier_str = str(self.get_identifier())
        block_dir = './chain-store/{}/blocks'.format(identifier_str)

        subdirs = block_dir.split('/')

        for i in range(1, len(subdirs)):
            dirpath = '/'.join(subdirs[0:i+1])
            
            if not os.path.exists(dirpath):
                os.makedirs(block_dir)
                break

        # walk files in the directory to pick up any block-X.json files
        for f in os.listdir(block_dir):
            m = re.search('^block-(\d+).json$', f)
                    
            if m is not None:
                # load json file
                block_file_path = '{}/{}'.format(block_dir, f)

                with open(block_file_path) as json_data:
                    block_json = json.load(json_data)

                    try:
                        block = Block.deserialize(block_json)

                        if self.last_block.timestamp >= block.timestamp:
                            break

                        self.add_block(block)
                    except Exception as e:
                        print("Failed to load block file {}; this may indicate corruption. You may try deleting the directory and rebuilding the database. The error was:\n\t{}".format(block_file_path, e))

    # load a contract via global identifier
    def load_contract(self, contract_identifier):
        pass

    # adds a block locally.
    def add_block(self, block, save=False):
        # verifications before we add to the chain
        # precondition-checking (block.verify()) should be done before this is called.
        if self.last_block is None:
            self.last_block = self.genesis_block

        assert block.prev_block_hash == self.last_block.block_hash, 'previous block hash does not match'
        assert block.timestamp > self.last_block.timestamp, 'block timestamp should be greater than previous block timestamp'

        #block.block_header.block_index = self.last_block.block_header.block_index + 1

        self.last_block = block

        if save:
            self.save_block(block)
    
    def save_block(self, block):
        identifier_str = str(self.get_identifier())
        block_dir = './chain-store/{}/blocks'.format(identifier_str)
        subdirs = block_dir.split('/')

        for i in range(1, len(subdirs)):
            dirpath = '/'.join(subdirs[0:i+1])
            
            if not os.path.exists(dirpath):
                os.makedirs(block_dir)
                break

        block_file_path = '{}/block-{}.json'.format(block_dir, block.timestamp)

        if os.path.exists(block_file_path):
            raise "block file already exists"

        with open(block_file_path, 'w') as outfile:
            json.dump(block.serialize(), outfile)

#clusterchain!
class TransactionSchema:
    def __init__(self, fields):
        self.fields = fields
        

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

class Block(Hashable):
    def __init__(self, block_header, timestamp, tx_set, prev_block_hash, nonce=None, block_hash=None):
        self.block_header = block_header
        self.timestamp = timestamp
        self.tx_set = tx_set
        self.prev_block_hash = prev_block_hash
        self.nonce = nonce
        self.block_hash = block_hash
        self._cache = {}
    
    def serialize(self):
        return {
            'block_header': self.block_header.serialize(),
            'timestamp': self.timestamp,
            'prev_block_hash': self.prev_block_hash,
            'nonce': self.nonce,
            'hash': self.block_hash,
            'tx_set': self.tx_set.serialize()
        }
    
    @classmethod
    def deserialize(kls, json_obj):
        REQUIRED_FIELDS = ['block_header', 'timestamp', 'tx_set', 'prev_block_hash', 'nonce', 'hash']
        
        for field in REQUIRED_FIELDS:
            assert field in json_obj, "'{}' is required in block data".format(field)
        
        block_header = BlockHeader.deserialize(json_obj['block_header'])

        assert isinstance(json_obj['timestamp'], int), 'timestamp should be int'
        assert json_obj['timestamp'] < int(time.time()), 'timestamp should be < now'
        
        assert isinstance(json_obj['tx_set'], list), 'tx_set should be list'
        tx_set_obj = TransactionSet.deserialize(json_obj['tx_set'])
        
        assert isinstance(json_obj['prev_block_hash'], str), 'prev_block_hash should be str'
        assert isinstance(json_obj['nonce'], int), 'nonce should be int'
        assert isinstance(json_obj['hash'], str), 'hash should be str'

        return Block(block_header=block_header, timestamp=json_obj['timestamp'], tx_set=tx_set_obj, prev_block_hash=json_obj['prev_block_hash'], nonce=json_obj['nonce'], block_hash=json_obj['hash'])
            
    def check_preconditions(self):
        errors = []

        current_time = int(time.time())

        if self.timestamp > current_time:
            errors.append("Block timestamp is greater than the current time ({} should be <= {}). Clock out of sync?".format(self.timestamp, current_time))

        # check each transaction to ensure the timestamp is < block timestamp
        for tx in self.tx_set.transactions:
            if tx.timestamp > self.timestamp:
                tx_hash = tx.calc_hash()
                errors.append("Transaction {} has a timestamp greater than the block timestamp. ({} must be <= {})".format(tx_hash, tx.timestamp, self.timestamp))

        return errors

    def verify(self):
        assert self.block_hash is not None, "block_hash should not be None for a pre-calculated block"
        
        errors = self.check_preconditions()

        if len(errors) == 0:
            recalculated_hash = self.calc_hash()

            if recalculated_hash == self.block_hash:
                return True
        else:
            print("The following preconditions failed while verifying the block: \n{}".format(list(map(lambda item: "\t * {}".format(item)))))

        return False
    
    def solve(self):
        assert self.nonce is None, "nonce should be None for unsolved blocks."
        
        self.nonce = -1
        self._cache = {}
        last_hash = None
        
        while last_hash is None or not last_hash.startswith('00000'):
            self.nonce += 1
            last_hash = self.calc_hash()

        self.block_hash = last_hash
        self._cache = {}
            
        print("block solved, hash = {}, nonce = {}".format(last_hash, self.nonce))
        
        return last_hash
    
    def calc_hash(self):
        assert self.nonce is not None, "nonce should not be None to calculate hash"
        assert self.nonce >= 0, "nonce should not be less than zero"

        if 'block_header_hash' not in self._cache:
          block_header_hash = self.block_header.calc_hash()
          print("block_header_hash = {}".format(block_header_hash))
          self._cache['block_header_hash'] = block_header_hash
        else:
          block_header_hash = self._cache['block_header_hash']

        if 'tx_hash' not in self._cache:
          tx_hash = self.tx_set.calc_hash()
          print("tx_hash = {}".format(tx_hash))
          self._cache['tx_hash'] = tx_hash
        else:
          tx_hash = self._cache['tx_hash']

        if 'timestamp_hash' not in self._cache:
          timestamp_hash = self.hash_str(str(self.timestamp))
          print("timestamp_hash = {}".format(timestamp_hash))
          self._cache['timestamp_hash'] = timestamp_hash
        else:
          timestamp_hash = self._cache['timestamp_hash']

        return self.hash_str(block_header_hash + tx_hash + timestamp_hash + str(self.nonce) + self.prev_block_hash)
"""
timestamp = 1525466988
tx_timestamp = 1525466987

print("timestamp = {}, tx_timestamp = {}".format(timestamp, tx_timestamp))

transactions = TransactionSet([
    Transaction('0x0', { 'value': 'Hello World' }, tx_timestamp)
])

blk = Block(block_header=BlockHeader(version='0.1-alpha'), timestamp=timestamp, tx_set=transactions, prev_block_hash='0x000')
print("blk = {}".format(blk))
print("hash = {}".format(blk.solve()))
is_correct_nonce = blk.verify()
assert is_correct_nonce, "incorrect nonce"
"""


GENESIS = Block.deserialize({
    'block_header': { 'version': '0.1-alpha' },
    'timestamp': 1525466988,
    'tx_set': [{
        'contract': '0x0',
        'data': { 'value': 'Hello World' },
        'timestamp': 1525466987
    }],
    'prev_block_hash': '0x000',
    'nonce': 2056510,
    'hash': '00000d2c9b4d799d73068f9e8e63c76865dd435dfc0314f4d968c83d6f6e789d'
})
is_correct_nonce = GENESIS.verify()
block_hash = GENESIS.calc_hash()
assert is_correct_nonce, "incorrect hash ({} != {})".format(GENESIS.block_hash, block_hash)

blockchain = Blockchain(GENESIS, GENESIS, BlockchainMetadata({
    'identifier': 'vivx.network.core-metachain',
    'contract-chain-identifier': 'core-metachain.Contracts',
    'version': '1',
    'owner': 'Andrew MacDonald',
    'genesis-timestamp': GENESIS.timestamp
}))
blockchain.load_blocks()

new_block = Block(
    block_header=BlockHeader(version='0.1-alpha'),
    timestamp=int(time.time()),
    tx_set=TransactionSet(transactions=[
        Transaction('0x0', { 'value': 'Block #2' }, int(time.time()))
    ]),
    prev_block_hash=blockchain.last_block.block_hash
)
new_block.solve()
new_block.verify()

blockchain.add_block(new_block, save=True)



# block_obj = Block.deserialize(block_dict)
# is_correct_nonce = block_obj.verify()
# block_hash = block_obj.calc_hash()
# assert is_correct_nonce, "incorrect hash ({} != {})".format(block_obj.block_hash, block_hash)



class BlockReceiver:
    def __init__(self):
        pass
    
    # take a serialized block, deserialize it and verify it by checking the nonce.
    # if it is not integrous, reject it. (how to deal with that?)
    #def receive_block(self, block_serialized):