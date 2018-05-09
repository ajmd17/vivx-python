import socket
import _thread
import json
import time
import datetime

from client import InvalidMessage
from object_identifier import ObjectIdentifier
from blockchain import BlockchainSyncState
from transaction import Transaction
from transaction_pool import TransactionPool
from metachain import get_subchain, metachain
from bootstrap import NODE_HUBS, select_node_hub
from miner import Miner

class Server:
    def __init__(self, onstatus):
        self.onstatus = onstatus

        self.socket = None
        self.clients = {}
        self.is_running = False
        self.node_hub = select_node_hub()
        self._tx_queue = []
        #self.miners = [
        #    Miner(blockchain=metachain)
        #]

    def start(self, address, port):
        assert not self.is_running

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((address, port))
            self.socket.listen(5)

            # have to get this working with public-facing addresses.
            self.inform_node_hub("http://{}:{}".format(address, port))

            #_thread.start_new_thread(self.update_tx_queue, ())
            _thread.start_new_thread(self.listen_for_connections, ())
            _thread.start_new_thread(self.load_metachain, ())

            #for miner in self.miners:
            #    miner.start_mining()

            self.is_running = True

            self.onstatus("Server is running")
        except Exception as e:
            self.onstatus("Failed to start server; Consider restarting the application. The error message was: {}".format(e))
            self.is_running = False

    def stop(self):
        assert self.is_running
        assert not self.socket is None

        self.socket.close()
        self.is_running = False
        self.clients = {}
        self.peers = []
        
        self.onstatus("Server not running")

    def _queue_tx(self, tx):
        self._tx_queue.append(tx)
        print("Tx queued to be sent to peers: {}".format(tx.serialize()))

    def inform_node_hub(self, address):
        assert self.node_hub is not None, "node hub not set"

        self.node_hub.post_self(address)

        _thread.start_new_thread(self.node_hub_heartbeat, (address,))

    def node_hub_heartbeat(self, address):
        assert self.node_hub is not None, "node hub not set"

        while self.is_running:
            self.node_hub.post_heartbeat(address)
            time.sleep(1)

    def load_metachain(self):
        self.onstatus("Loading metachain locally...")
        metachain.sync_state = BlockchainSyncState.SYNCING
        metachain.load_blocks()
        metachain.sync_state = BlockchainSyncState.SYNCED

    def update_tx_queue(self):
        while self.is_running:
            while len(self._tx_queue) != 0:
                tx_obj = self._tx_queue[0]
                tx_serialized = tx_obj.serialize()

                for key, value in self.clients.items():
                    value.send(json.dumps({
                        'type': 'recvtx',
                        'tx': tx_serialized
                    }).encode('utf-8'))

                self._tx_queue.pop(0)

            time.sleep(0.5)

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
        print("message: {}".format(obj))
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

        elif msg_type == "pushtx":
            print("pushtx")
            if obj["tx"] is None:
                raise InvalidMessage(obj)

            if obj["blockchain"] is None:
                raise InvalidMessage(obj)

            tx = None

            try:
                tx = Transaction.deserialize(obj["tx"])
            except Exception as e:
                print("Error deserializing tx: {}".format(e))
                raise InvalidMessage(obj)


            # lets have all servers connected to a set (maybe 8) other independent servers.
            # when we broadcast a transaction to all these nodes, they will broadcast it to their connected nodes as well.
            #for key, value in self.clients.items():
            #    value.send({
            #        'type': 'recvtx',
            #        'tx': tx.serialize()
            #    })
                #print(key, value)

            TransactionPool.instance.queue_tx(tx)

            # =====

            # TODO: this could ping the host node with the transaction,
            # allowing it to be sent to miner nodes to be verified + mined into the chain.
            # this is just a prototype though.

            # TODO get the blockchain object via the passed blockchain parameter, so we can mine the tx.
            #print("miner = {}".format(self.miners[0]))
            #self.miners[0].queue_tx(atx.serialize())
            #for hub in NODE_HUBS:
            #    addr, port = self.socket.getsockname()
                # TODO: make address be the server's publicly accessible address
            #     hub.posttx(address="http://{}:{}".format(addr, port), tx=tx.serialize())

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

                if counter > 0 and start_index == -1:
                    # possible fork has occurred, last block hash given by client and metachain should be in sync at this point.
                    raise "possible fork occurred: last block hash given by client ({}) not found after sync. \
                           The fork may have occurred from the client side or from the source that the blocks were synced from previously.".format(last_block_hash)

            print("start_index = {}".format(start_index))

            # TODO: Find a way to cache this data

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