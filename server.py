import socket
import _thread
import json
import time
import datetime

from client import InvalidMessage

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
            }))
        # TODO: messages here
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