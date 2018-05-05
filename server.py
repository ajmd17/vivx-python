import socket
import _thread
import json
import time
import datetime

from client import InvalidMessage
from object_identifier import ObjectIdentifier
from blockchain import BlockchainSyncState
from metachain import get_subchain, metachain

class Server:
    def __init__(self, onstatus):
        self.onstatus = onstatus

        self.socket = None
        self.clients = {}
        self.is_running = False

    def start(self, address, port):
        assert not self.is_running

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((address, port))
            self.socket.listen(5)

            _thread.start_new_thread(self.listen_for_connections, ())
            _thread.start_new_thread(self.load_metachain, ())

            self.is_running = True

            self.onstatus("Server is running")
        except Exception as e:
            self.onstatus("Failed to start server; Consider restarting the application. The error message was: {}".format(e))

    def stop(self):
        assert self.is_running
        assert not self.socket is None

        self.socket.close()
        self.is_running = False
        self.clients = {}
        self.peers = []
        
        self.onstatus("Server not running")

    def load_metachain(self):
        self.onstatus("Loading metachain locally...")
        metachain.sync_state = BlockchainSyncState.SYNCING
        metachain.load_blocks()
        metachain.sync_state = BlockchainSyncState.SYNCED

    def add_client(self, client_socket, client_address):
        assert self.is_running

        self.clients["%s:%s" % client_address] = client_socket
        _thread.start_new_thread(self.handle_client_messages, (client_socket, client_address))
        # self.onstatus("Server is running ({} active connections)".format(len(self.clients)))

    def remove_client(self, client_socket, client_address):
        del self.clients["%s:%s" % client_address]
        # self.onstatus("Server is running ({} active connections)".format(len(self.clients)))

    def listen_for_connections(self):
        while self.is_running:
            try:
                client_socket, client_address = self.socket.accept()
                client_socket.settimeout(2)
                self.add_client(client_socket, client_address)
            except:
                break
        
        if self.is_running:
            self.stop()

    def respond_to_command(self, client_socket, obj):
        msg_type = obj["type"]

        if msg_type is None:
            raise InvalidMessage(obj)

        if msg_type == 'ping':
            client_socket.send(json.dumps({
                'type': 'pong'
            }).encode('utf-8'))
        elif msg_type == "get_chain_metadata":
            if obj["identifier"] is None:
                raise InvalidMessage(obj)

            if obj["last_block_hash"] is None:
                raise InvalidMessage(obj)

            identifier = None

            try:
                identifier = ObjectIdentifier.parse(obj["identifier"])
            except:
                raise InvalidMessage(obj)

            _thread.start_new_thread(self.sync_blockchain_for_client, (client_socket, identifier, obj["last_block_hash"]))
            #get_subchain(identifier)

        elif msg_type == "broadcast":
            if obj["msg"] is None:
                raise InvalidMessage(obj)

            self.socket.sendall(obj["msg"])

    def handle_client_messages(self, client_socket, client_address):
        while self.is_running:
            try:
                data = client_socket.recv(1024)

                if (not data) or len(data) == 0:
                    break

                obj = None

                try:
                    obj = json.loads(data)
                except:
                    raise InvalidMessage(data)

                self.respond_to_command(client_socket, obj)

            except InvalidMessage as e:
                self.onstatus(str(e))
                continue

            except Exception as e:
                break

        self.remove_client(client_socket, client_address)

    def sync_blockchain_for_client(self, client_socket, identifier, last_block_hash=None):
        # TODO: assert that this node responds to that blockchain.
        # check if the blockchain exists locally, and verify with other peers.
        # if it does not exist locally, we have to sync in here, first.
        self.onstatus("Sync requested for blockchain with identifier {}".format(identifier))

        if identifier == metachain.get_identifier():
            print("metachain sync requested...")

            assert metachain.sync_state != BlockchainSyncState.UNSYNCED, "metachain sync state should not be UNSYNCED, sync should have started previously"

            if metachain.sync_state == BlockchainSyncState.SYNCING:
                print("sync is currently in progress. waiting...")

            # poll until it is synced
            while metachain.sync_state != BlockchainSyncState.SYNCED:
                print("waiting...")
                time.sleep(0.5)

            # TODO: ensure sync state is OK.

            # feed each block to the client
            start_index = 0
            page_size = 10

            if last_block_hash is not None:
                start_index = -1

                # find block with hash - TODO: optimize this!
                counter = 0

                for block_page in metachain.page_block_files(pagesize=page_size):
                    block_hashes = list(map(lambda block_file_path: metachain.load_block_file(block_file_path).block_hash, block_page))
                    hash_index = block_hashes.index(last_block_hash)

                    if hash_index is not None:
                        start_index = counter + hash_index + 1
                        break
                    else:
                        counter += page_size

                if start_index == -1:
                    # possible fork has occurred, last block hash given by client and metachain should be in sync at this point.
                    raise "possible fork occurred: last block hash given by client ({}) not found after sync. \
                           The fork may have occurred from the client side or from the source that the blocks were synced from previously.".format(last_block_hash)

            print("start_index = {}".format(start_index))

            for block_page in metachain.page_block_files(start=start_index // page_size, pagesize=page_size):
                block_page_start_index = start_index - ((start_index // page_size) * page_size)
                serialized_blocks = []

                for block in block_page[block_page_start_index:]:
                    serialized_blocks.append(metachain.load_block_file(block).serialize())

                if len(serialized_blocks) == 0:
                    print("No blocks to send - client is in sync")
                    break

                client_socket.send(json.dumps({
                    'type': 'recvblockpage',
                    'blockpage': serialized_blocks
                }).encode('utf-8'))

                time.sleep(2)