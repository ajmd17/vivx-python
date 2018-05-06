import time
import _thread

from block import Block
from block_header import BlockHeader
from transaction import Transaction
from transaction_set import TransactionSet

class Miner:
  def __init__(self, blockchain):
    self.blockchain = blockchain
    self.tx_queue = TransactionSet(transactions=[])
    self.is_mining = False

  def queue_tx(tx):
    self.tx_queue.add_tx(tx)

  def start_mining(self):
    self.is_mining = True
    _thread.start_new_thread(self._mine, ())

  def stop_mining(self):
    self.is_mining = False

  def _mine(self):
    byte_size = 0

    block_header = BlockHeader(version='0.1-alpha')
    
    while self.is_mining:
      #print("mining")
      current_block = Block(block_header=block_header, timestamp=int(time.time()), tx_set=self.tx_queue, prev_block_hash=self.blockchain.last_block.block_hash)
      try:
        for tx in self.tx_queue.transactions:
          # calculate byte size
          tx_serialized = tx.serialize()
          tx_bytes = bytes(tx_serialized)
          print("tx = {}".format(tx_serialized))
      except Exception as e:
        print("error: {}".format(e))

      time.sleep(1)