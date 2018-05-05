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

    






from block import Block
from blockchain import Blockchain
from block_header import BlockHeader
from blockchain_metadata import BlockchainMetadata
from transaction import Transaction
from transaction_set import TransactionSet
from genesis import genesis_block

#clusterchain!
class TransactionSchema:
    def __init__(self, fields):
        self.fields = fields


blockchain = Blockchain(genesis_block, genesis_block, BlockchainMetadata({
    'identifier': 'vivx.network.core-metachain',
    'contract-chain-identifier': 'core-metachain.Contracts',
    'version': '1',
    'owner': 'Andrew MacDonald',
    'genesis-timestamp': genesis_block.timestamp
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