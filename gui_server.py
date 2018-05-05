from tkinter import *
from tkinter.ttk import *
import socket
import _thread
import json
import time
import datetime

from client import *
from server import *

class P2PServer(Frame):
    def __init__(self, root):
        Frame.__init__(self, root)
        self.root = root

        self.client = Client(
            {
                'onconnect': self._onselfconnect,
                'ondisconnect': self._onselfdisconnect,
                'onfailure': self._onselffailure,
                'onstatus': self.client_status,
                'onerror': self.client_error
            }
        ) # so it can connect to other servers as a client
    
        self.server = Server(
            onstatus=self.server_status
        )

    def _onselfconnect(self):
        self.client_status("Connected to server successfully")
        self.connect_to_server_button.config(text="Disconnect", command=self.disconnect_from_server)
    
    def _onselfdisconnect(self):
        self.client_status("Client not connected")
        self.connect_to_server_button.config(text="Connect", state=NORMAL, command=self.connect_to_server)
    
    def _onselffailure(self, e):
        self.client_status("Failed to connect to server: {}".format(e))

    def show(self):
        self.root.title("VIVX Clusternode")

        parent_frame = Frame(self.root)
        parent_frame.grid(padx=10, pady=10, sticky=E+W+N+S)

        self._create_start_server_frame(parent_frame)
        self._create_connect_to_server_frame(parent_frame)
        self._create_log_frame(parent_frame)

    def _create_start_server_frame(self, parent_frame):
        server_info_frame = Frame(parent_frame)

        server_info_label = Label(server_info_frame, text="Run Server")
        server_info_label.grid(row=0, column=0)

        self.address_var = StringVar()
        self.address_var.set("127.0.0.1")

        address_label = Label(server_info_frame, text="Address:")
        address_label.grid(row=1, column=0)

        self.address_field = Entry(server_info_frame, width=15, textvariable=self.address_var)
        self.address_field.grid(row=1, column=1)

        self.port_var = StringVar()
        self.port_var.set("8090")

        port_label = Label(server_info_frame, text="Port:")
        port_label.grid(row=1, column=2, padx=5)

        self.port_field = Entry(server_info_frame, width=5, textvariable=self.port_var)
        self.port_field.grid(row=1, column=3)

        self.start_server_button = Button(server_info_frame, text="Start Server", command=self.start_server)
        self.start_server_button.grid(row=1, column=4, padx=(5, 0))

        bottom_frame = Frame(server_info_frame)

        #self.server_status_label = Label(bottom_frame, text="Server not running")
        #self.server_status_label.grid(row=2, column=0, sticky=W)

        bottom_frame.grid(row=2, column=0, sticky=E+W+S, pady=(5, 0))

        server_info_frame.grid(row=0, column=0, sticky=W+E)

    def _create_connect_to_server_frame(self, parent_frame):
        connect_to_server_frame = Frame(parent_frame)

        connect_to_server_label = Label(connect_to_server_frame, text="Connect to Server")
        connect_to_server_label.grid(row=0, column=0)

        self.connect_address_var = StringVar()
        self.connect_address_var.set("127.0.0.1")

        address_label = Label(connect_to_server_frame, text="Address:")
        address_label.grid(row=1, column=0)

        self.connect_address_field = Entry(connect_to_server_frame, width=15, textvariable=self.connect_address_var)
        self.connect_address_field.grid(row=1, column=1)

        self.connect_port_var = StringVar()
        self.connect_port_var.set("8090")

        port_label = Label(connect_to_server_frame, text="Port:")
        port_label.grid(row=1, column=2, padx=5)

        self.connect_port_field = Entry(connect_to_server_frame, width=5, textvariable=self.connect_port_var)
        self.connect_port_field.grid(row=1, column=3)

        self.connect_to_server_button = Button(connect_to_server_frame, text="Connect", command=self.connect_to_server)
        self.connect_to_server_button.grid(row=1, column=4, sticky=E+W, padx=(5, 0))
        
        bottom_frame = Frame(connect_to_server_frame)

        #self.client_status_label = Label(bottom_frame, text="Client not connected")
        #self.client_status_label.grid(row=2, column=0, sticky=W)

        bottom_frame.grid(row=2, column=0, sticky=E+W+S, pady=(5, 0))

        connect_to_server_frame.grid(row=1, column=0, sticky=W+E)

    def _create_log_frame(self, parent_frame):
        nb = Notebook(parent_frame)
        nb.grid(row=3, column=0, columnspan=50, rowspan=49, sticky=N+S+W+E)

        log_frame = Frame(parent_frame)

        self.text_area = Text(log_frame, height=15)
        self.text_area.grid(row=1, column=1, sticky=N+E+W+S)

        nb.add(log_frame, text='Log')


        create_new_transaction_frame = Frame(parent_frame)

        create_new_transaction_label = Label(create_new_transaction_frame, text="Create New Transaction")
        create_new_transaction_label.grid(row=0, column=0)

        self.create_new_transaction_field = Text(create_new_transaction_frame, height=15)
        self.create_new_transaction_field.grid(row=1, column=0, sticky=N+E+W+S)

        create_new_transaction_button = Button(create_new_transaction_frame, text="Create", command=self.create_new_transaction)
        create_new_transaction_button.grid(row=2, column=0)

        nb.add(create_new_transaction_frame, text='Create Transaction')

    def _reset_new_transaction_text(self):
        latest = self.blockchains['tx'].latestblock()
        self.create_new_transaction_field.delete(1.0, END)
        self.create_new_transaction_field.insert(END, '{{\n  "blockid": {},\n  "timestamp": "{}",\n  "parent": {},\n  "data": {{\n    "sender": "",\n    "receiver": "",\n    "amt": 0\n  }}\n}}'.format(latest.blockid + 1, datetime.datetime.now(), latest.blockid))

    def create_new_transaction(self):
        from transaction import Transaction
        from metachain import metachain as mc
        # TODO: ability to select the blockchain to push to.
        text_value = self.create_new_transaction_field.get("1.0", END)

        try:
            json_tx = {}
            # adjust timestamp.
            json_tx['contract'] = '0x0'
            json_tx['data'] = json.loads(text_value)
            json_tx['timestamp'] = datetime.datetime.now()

            self.client.broadcast_transaction(Transaction.deserialize(json_tx))

            self.client_status("Broadcasting transaction...")

            self.blockchains['tx'].blocks.append(tx)
            tx.savelocal(self.blockchains['tx'])

            tkMessageBox.showinfo("Transaction created", "The transaction has been successfully created, and will begin propagating throughout the network.")
            self._reset_new_transaction_text()

        except AssertionError as e:
            tkMessageBox.showerror("Validation failed", str(e))

        except ValueError as e:
            tkMessageBox.showerror("Invalid JSON data", str(e))
            self._reset_new_transaction_text()


    def log(self, message):
        self.text_area.insert(END, "{}: {}\n".format(str(datetime.datetime.now()), message))

    def connect_to_server(self):
        self.client.connect(self.connect_address_var.get().replace(' ', ''), int(self.connect_port_var.get().replace(' ', '')))

    def disconnect_from_server(self):
        self.client.disconnect()
        self.client_status('Disconnecting from server...')
        self.connect_to_server_button.config(state=DISABLED)

    def start_server(self):
        self.server.start(self.address_var.get().replace(' ', ''), int(self.port_var.get().replace(' ', '')))
        self.start_server_button.config(text="Stop Server", command=self.stop_server)

    def stop_server(self):
        self.server.stop()
        self.start_server_button.config(text="Start Server", command=self.start_server)

    def _status(self, status_label, msg, timeout=None):
        status_label.config(text=msg)
        self.log(msg)

        if not timeout is None:
           _thread.start_new_thread(lambda: time.sleep(timeout) or self._status(status_label, ""), ())

    def server_status(self, msg, timeout=None):
        #self._status(self.server_status_label, msg, timeout)
        self.log(msg)

    def client_status(self, msg, timeout=None):
        #self._status(self.client_status_label, msg, timeout)
        self.log(msg)

    def client_error(self, msg, timeout=None):
        #self._status(self.client_status_label, '*** ERROR ***: {}'.format(msg), timeout)
        self.log('*** ERROR ***: {}'.format(msg))


def main():
    root = Tk()

    p2p_server = P2PServer(root)
    p2p_server.show()

    root.mainloop()

if __name__ == '__main__':
    main()