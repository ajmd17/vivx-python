import time
import json
import os

from block_header import BlockHeader
from transaction_set import TransactionSet
from utility_classes import Hashable

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
        
    def get_block_filename(self, block_dir):
        return '{}/block-{}.json'.format(block_dir, self.timestamp)

    def save(self, block_dir):
        block_file_path = self.get_block_filename(block_dir)

        if os.path.exists(block_file_path):
            raise Exception("block file already exists")

        with open(block_file_path, 'w') as outfile:
            json.dump(self.serialize(), outfile)