import os
import json
from block import Block

genesis_block = None

def generate_genesis_block():
    import time
    from transaction_set import TransactionSet
    from transaction import Transaction
    from object_identifier import ObjectIdentifier
    from block_header import BlockHeader

    block = Block(
        block_header=BlockHeader(version='0.1-alpha'),
        timestamp=int(time.time()),
        tx_set=TransactionSet(transactions=[
            Transaction(
                contract_identifier=ObjectIdentifier.parse('vivx.network.core-metachain.BlockchainEntry'),
                # data should fit the schema of BlockchainMetadata.
                data={
                    'identifier': 'vivx.network.sidechain',
                    'contract-chain-identifier': '',
                    'version': '0.1-alpha',
                    'owner': 'VIVX',
                    'genesis-timestamp': int(time.time())
                },
                timestamp=int(time.time())
            )
        ]),
        prev_block_hash='0'
    )

    block.solve()
    block.verify()

    return block

if __name__ == '__main__':
    genesis_block = generate_genesis_block()
    genesis_block.save('./', filename='genesis.json')
else:
    with open('./genesis.json') as file:
        genesis_block = Block.deserialize(json.load(file))
    # genesis_block = Block.deserialize({
    #     'block_header': { 'version': '0.1-alpha' },
    #     'timestamp': 1525466988,
    #     'tx_set': [{
    #         'contract': 'vivx.network.core-metachain.BlockchainEntry',
    #         'data': { 'value': 'Hello World' },
    #         'timestamp': 1525466987
    #     }],
    #     'prev_block_hash': '0x000',
    #     'nonce': 2056510,
    #     'hash': '00000d2c9b4d799d73068f9e8e63c76865dd435dfc0314f4d968c83d6f6e789d'
    # })
    is_correct_nonce = genesis_block.verify()
    block_hash = genesis_block.calc_hash()
    assert is_correct_nonce, "incorrect hash ({} != {})".format(genesis_block.block_hash, block_hash)
