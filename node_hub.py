import requests

class NodeHub:
    def __init__(self, remote_address):
        self.remote_address = remote_address

    def healthcheck(self):
        pass

    def post_heartbeat(self, address):
        r = requests.post('{}/heartbeat'.format(self.remote_address), data={ 'address': address })

        if r.status_code != 200:
            json_data = r.json()
            raise Exception(json_data['error'])

    # post this server to be publicly visible from the node hub
    def post_self(self, address):
        r = requests.post('{}/nodes'.format(self.remote_address), data={ 'address': address })

        if r.status_code != 200:
            json_data = r.json()
            raise Exception(json_data['error'])

    # get nodes on this hub
    def get_nodes(self):
        r = requests.get('{}/nodes'.format(self.remote_address))

        json_data = r.json()

        if r.status_code != 200:
            raise Exception(json_data['error'])

        assert isinstance(json_data, list)

        return json_data