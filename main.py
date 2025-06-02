import socket
import threading
import json
import sys
from datetime import datetime

# --------- Blockchain classes ----------

class Block:
    def __init__(self, index, previous_hash, timestamp, data, nonce=0, hash=None):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.data = data
        self.nonce = nonce
        self.hash = hash or self.calculate_hash()

    def calculate_hash(self):
        import hashlib
        block_string = f"{self.index}{self.previous_hash}{self.timestamp}{json.dumps(self.data)}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "data": self.data,
            "nonce": self.nonce,
            "hash": self.hash
        }

    @staticmethod
    def from_dict(d):
        return Block(d['index'], d['previous_hash'], d['timestamp'], d['data'], d['nonce'], d['hash'])


class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        genesis_data = {
            "product_id": "GENESIS",
            "status": "Genesis Block",
            "location": "N/A",
            "timestamp": datetime.utcnow().isoformat()
        }
        return Block(0, "0", datetime.utcnow().isoformat(), genesis_data)

    def latest_block(self):
        return self.chain[-1]

    def add_block(self, block):
        if self.is_valid_new_block(block, self.latest_block()):
            self.chain.append(block)
            return True
        return False

    def is_valid_new_block(self, new_block, previous_block):
        if previous_block.index + 1 != new_block.index:
            return False
        if previous_block.hash != new_block.previous_hash:
            return False
        if new_block.calculate_hash() != new_block.hash:
            return False
        return True

    def mine_block(self, data):
        previous_block = self.latest_block()
        index = previous_block.index + 1
        timestamp = datetime.utcnow().isoformat()
        nonce = 0

        new_block = Block(index, previous_block.hash, timestamp, data, nonce)

        difficulty = 3
        target = "0" * difficulty

        while not new_block.hash.startswith(target):
            new_block.nonce += 1
            new_block.hash = new_block.calculate_hash()

        return new_block

    def get_product_history(self, product_id):
        return [blk for blk in self.chain if blk.data.get("product_id") == product_id]

# --------- Node & Networking ---------

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
PEERS = []
blockchain = Blockchain()

lock = threading.Lock()  # for thread-safe blockchain access

def handle_client(conn, addr):
    with conn:
        data = conn.recv(4096)
        if not data:
            return
        command_line = data.decode().strip()
        response = process_command(command_line)
        conn.sendall(response.encode())

def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', PORT))
    s.listen(5)
    print(f"Server listening on port {PORT} ...")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

def process_command(cmd_line):
    parts = cmd_line.split()
    if not parts:
        return "Invalid command"

    cmd = parts[0].lower()

    if cmd == "connect":
        if len(parts) != 3:
            return "Usage: connect <ip> <port>"
        ip = parts[1]
        try:
            port = int(parts[2])
        except:
            return "Invalid port number"
        return connect_peer(ip, port)

    elif cmd == "mine":
        if len(parts) < 4:
            return "Usage: mine <product_id> <status> <location>"
        product_id = parts[1]
        status = parts[2]
        location = " ".join(parts[3:])
        data = {
            "product_id": product_id,
            "status": status,
            "location": location,
            "timestamp": datetime.utcnow().isoformat()
        }
        return mine_and_broadcast(data)

    elif cmd == "history":
        if len(parts) != 2:
            return "Usage: history <product_id>"
        product_id = parts[1]
        return get_history_str(product_id)

    elif cmd == "chain":
        return get_chain_summary()

    elif cmd == "peers":
        return f"Connected peers: {len(PEERS)}"

    else:
        return "Unknown command"

def connect_peer(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        PEERS.append(s)
        return f"Connected to peer {ip}:{port}"
    except Exception as e:
        return f"Failed to connect to {ip}:{port} - {e}"

def mine_and_broadcast(data):
    with lock:
        new_block = blockchain.mine_block(data)
        blockchain.add_block(new_block)
    broadcast_block(new_block)
    return f"Block mined: index={new_block.index}, product={data['product_id']}"

def get_history_str(product_id):
    with lock:
        history = blockchain.get_product_history(product_id)
    if not history:
        return f"No history found for product ID: {product_id}"
    lines = []
    for blk in history:
        d = blk.data
        lines.append(f"[{blk.index}] {d['timestamp']} - {d['status']} at {d['location']} (hash: {blk.hash[:8]}...)")
    return "\n".join(lines)

def get_chain_summary():
    with lock:
        chain = blockchain.chain.copy()
    lines = []
    for blk in chain:
        d = blk.data
        lines.append(f"[{blk.index}] {d['product_id']} - {d['status']} at {d['location']}")
    return "\n".join(lines)

def broadcast_block(block):
    msg = json.dumps({"type": "NEW_BLOCK", "data": block.to_dict()}).encode()
    dead_peers = []
    for peer in PEERS:
        try:
            peer.sendall(msg)
        except:
            dead_peers.append(peer)
    for dp in dead_peers:
        PEERS.remove(dp)

if __name__ == "__main__":
    start_server()
