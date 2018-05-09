import _thread
import time

from transaction import Transaction

# a global singleton transaction pool
class TransactionPool:
    class TransactionPoolSingleton:
        def __init__(self, server, client):
            self.server = server
            self.client = client
            self.tx_queue = []
            self._loop_thread = None
            self.running = False

        def enqueue(self, tx):
            assert isinstance(tx, Transaction)
            self.tx_queue.append(tx)

        def start(self):
            self.running = True
            self._loop_thread = _thread.start_new_thread(self.loop, ())

        def stop(self):
            self.running = False

        def loop(self):
            while self.running:
                while len(self.tx_queue) != 0:
                    print("TEST")
                    tx_obj = self.tx_queue[0]
                    tx_serialized = tx_obj.serialize()

                    # TODO: possibly verify the tx first ? (double-check)

                    for key, value in self.server.clients.items():
                        value.send(json.dumps({
                            'type': 'recvtx',
                            'tx': tx_serialized
                        }).encode('utf-8'))

                    self.tx_queue.pop(0)

                time.sleep(2)



    instance = None

    def __init__(self, server, client):
        if not TransactionPool.instance:
            TransactionPool.instance = TransactionPool.TransactionPoolSingleton(server, client)
        else:
            TransactionPool.instance.server = server
            TransactionPool.instance.client = client

    
