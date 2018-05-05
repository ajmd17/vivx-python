import os
import re
import json

from object_identifier import ObjectIdentifier
from block import Block
from utility_classes import Identifiable

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