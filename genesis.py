import os
from block import Block

genesis_block = Block.deserialize({
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
is_correct_nonce = genesis_block.verify()
block_hash = genesis_block.calc_hash()
assert is_correct_nonce, "incorrect hash ({} != {})".format(genesis_block.block_hash, block_hash)