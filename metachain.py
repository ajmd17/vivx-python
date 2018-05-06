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

# TODO: Make Metachain a dervied class of Blockchain and move these methods to it
def get_subchains():
    for block_page in metachain.page_block_files():
        blocks = [metachain.load_block_file(block_file_path) for block_file_path in block_page]
        tx_sets = [block.tx_set for block in blocks]
        txs = [tx for sublist in [tx_set.transactions for tx_set in tx_sets] for tx in sublist if tx.contract_identifier == 'vivx.network.core-metachain.BlockchainEntry']#[tx for tx in tx_set.transactions for tx_set in tx_sets]

def get_subchain(identifier):
    print("identifier = {}".format(identifier))
    for block in metachain.blocks:
        print("block = {}".format(block))