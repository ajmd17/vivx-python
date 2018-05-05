import _thread
import socket
import json
import time
from functools import reduce

from object_identifier import ObjectIdentifier
from metachain import metachain as mc
from block import Block

class InvalidMessage(Exception):
    def __init__(self, msg):
        self.msg = "Invalid message: {}".format(msg)

class Client:
    def __init__(self, handlers):
        self.handlers = handlers

        self.socket = None
        self.peers = []
        self.is_connected = False

    def connect(self, server_address, server_port):
        assert not self.is_connected
        _thread.start_new_thread(self._connect, (server_address, server_port))

    def _connect(self, server_address, server_port):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(3)
            self.socket.connect((server_address, server_port))
            self.is_connected = True

            _thread.start_new_thread(self.listen_for_server_messages, ())
            _thread.start_new_thread(self.periodically_resync_with_peers, ())
            _thread.start_new_thread(self.sync_metachain, ())

            self.handlers['onconnect']()
        except Exception as e:
            self.handlers['onfailure'](e)

    def disconnect(self):
        assert self.is_connected
        assert not self.socket is None

        self.socket.close()
        self.is_connected = False

        #if self.is_connected:
        #    _thread.start_new_thread(self.periodically_resync_with_peers, ())

    def broadcast_transaction(self, tx):
        try:
            self.socket.send(json.dumps({
                'type': 'pushtx',
                'tx': tx.serialize()
            }).encode('utf-8'))
        except Exception as e:
            print("Failed to broadcast tx: {}".format(e))
            raise e

    def respond_to_message(self, obj):
        msg_type = obj["type"]

        if msg_type is None:
            raise InvalidMessage(obj)

        if msg_type == "pong":
            pass
        elif msg_type == "recvblockpage":
            print("recvblockpage", obj)

            blockpage = obj["blockpage"]

            assert isinstance(blockpage, list), 'blockpage should be list'

            for block_json in blockpage:
                # load serialized block object
                block_obj = Block.deserialize(block_json)
                assert block_obj.prev_block_hash == mc.last_block.block_hash, "requested block object prev_block_hash ({}) should be equal to the block hash of the previous block in the local chain ({})".format(block_obj.prev_block_hash, mc.last_block.block_hash)

                mc.add_block(block_obj, save=True)

        elif msg_type == "updatepeers":
            self._updatepeers(obj["peers"])

    def listen_for_server_messages(self):
        _thread.start_new_thread(self.heartbeat, ())

        while 1:
            if not self.is_connected:
                return

            try:
                data = self.socket.recv(1024)

                if not data:
                    break

                obj = None

                try:
                    obj = json.loads(data)
                except:
                    raise InvalidMessage(data)

                self.respond_to_message(obj)

            except InvalidMessage as e:
                self.handlers['onstatus'](str(e))
                continue

            except Exception as e:
                print("Error while listening for server messages: {}".format(e))
                break

        if self.is_connected:
            self.disconnect()

        self.handlers['ondisconnect']()

    def heartbeat(self):
        while self.is_connected:
            self.socket.send(json.dumps({
                'type': 'ping'
            }).encode('utf-8'))

            time.sleep(1)
    
    def sync_metachain(self):
        print("Loading local metachain blocks...")
        mc.load_blocks()

        print("Syncing metachain (wait 5s...)")
        time.sleep(5)

        print("mc.last_block.block_hash = {}".format(mc.last_block.block_hash))

        # load latest copy of the metachain
        self.socket.send(json.dumps({
            'type': 'get_chain_metadata',
            'identifier': str(mc.get_identifier()),
            'last_block_hash': mc.last_block.block_hash
        }).encode('utf-8'))

        # when we get data from the metachain,
        # we can start to pull other blockchains that are nested within the metachain.

    def periodically_resync_with_peers(self):
        while self.is_connected:
          if not self.is_connected:
            return

          time.sleep(5)

    def _updatepeers(self, peerlist):
        self.peers = peerlist
