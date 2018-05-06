import requests
import time

from node_hub import NodeHub

NODE_HUBS = [
    NodeHub(remote_address='http://127.0.0.1:8080')
]

# this method is used to select a node hub for the server to connect to
# this could be region-based to make data transfer faster,
# and also could be randomized to a degree to protect decentralization

# we need some kind of hub reputation tracker that can be stored on a blockchain.
# this could prevent malicious actors from running a node custom-coded to not broadcast transactions,
# for example...

def select_node_hub():
    node_hub = None

    for hub in NODE_HUBS:
        errors = []
        # ping it
        r = requests.get(hub.remote_address)
        
        if r.status_code == 200:
            try:
                response_json = r.json()

                assert 'startTime' in response_json
                assert isinstance(response_json['startTime'], int)
                assert 'timestamp' in response_json
                assert isinstance(response_json['timestamp'], int)
                assert 'version' in response_json
                assert isinstance(response_json['version'], str)
                assert 'node-identifier' in response_json
                assert isinstance(response_json['node-identifier'], str)

                # TODO version compatibility check

                ts = int(time.time())
                node_hub_ts = response_json['timestamp']

                assert abs(ts - node_hub_ts) <= 30, 'node hub timestamp is out of sync with system timestamp. (node hub: {}, system: {})'.format(node_hub_ts, ts)

                node_hub = hub
                break
            except Exception as e:
                errors.append(str(e))
        else:
            errors.append("healthcheck failed")

        if len(errors) != 0:
            print("not connecting to node hub {}; moving to next. reasons:\n\t{}".format(hub.remote_address, '\n'.join(list(map(lambda item: "\t{}".format(item), errors)))))

    if node_hub is None:
        raise Exception("attempted connection failed for all node hubs")

    return node_hub