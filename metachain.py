from blockchain import Blockchain
from blockchain_metadata import BlockchainMetadata
from genesis import genesis_block

metachain = Blockchain(genesis_block, genesis_block, BlockchainMetadata({
    'identifier': 'vivx.network.core-metachain',
    'contract-chain-identifier': 'core-metachain.Contracts',
    'version': '1',
    'owner': 'Andrew MacDonald',
    'genesis-timestamp': genesis_block.timestamp
}))
#metachain.load_blocks()

def get_subchain(identifier):
    print("identifier = {}".format(identifier))
    for block in metachain.blocks:
        print("block = {}".format(block))