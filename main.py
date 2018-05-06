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
from transaction import Transaction
from transaction_set import TransactionSet
from genesis import genesis_block
from object_identifier import ObjectIdentifier

#clusterchain!
class TransactionSchema:
    def __init__(self, fields):
        self.fields = fields


# from metachain import metachain as mc

# new_block = Block(
#     block_header=BlockHeader(version='0.1-alpha'),
#     timestamp=int(time.time()),
#     tx_set=TransactionSet(transactions=[
#         Transaction(ObjectIdentifier.parse('vivx.network.core-metachain.BlockchainEntry'), { 'value': 'Block #2' }, int(time.time()))
#     ]),
#     prev_block_hash=mc.last_block.block_hash
# )
# new_block.solve()
# new_block.verify()

# mc.add_block(new_block, save=True)


from bytecode import Bytecode
from bytecode_parser import BytecodeParser
from vm import VM
from instruction import *


def test_bytecode():

    bc = Bytecode(instructions=[
        Instruction(Opcode.PUSH, [Value(ValueType.INT, 123)]),
        Instruction(Opcode.PUSH, [Value(ValueType.INT, 456)]),
        Instruction(Opcode.ADD)
        #Instruction(Opcode.POP)
    ])

    errors = BytecodeParser.analyze(bc)

    if len(errors) != 0:
      print("Errors in bytecode found:\n\t{}".format('\n\t'.join(errors)))
      return

    vm = VM(bc)

    try:
      vm.evaluate()
      print("stack = {}".format(vm.stack))
    except Exception as e:
      print("Evaluation exception: {}".format(e))

test_bytecode()

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