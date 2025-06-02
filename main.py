import socket
import threading
import json
import sys
import time
from datetime import datetime

# --- Blockchain & Block classes ---

class Block:
    def __init__(self, index, previous_hash, timestamp, data, nonce=0, hash=None):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.data = data  # data is a dict with supply chain info
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
            print("Invalid index")
            return False
        if previous_block.hash != new_block.previous_hash:
            print("Invalid previous hash")
            return False
        if new_block.calculate_hash() != new_block.hash:
            print("Invalid hash")
            return False
        return True

    def mine_block(self, data):
        previous_block = self.latest_block()
        index = previous_block.index + 1
        timestamp = datetime.utcnow().isoformat()
        nonce = 0

        new_block = Block(index, previous_block.hash, timestamp, data, nonce)

        # Simple Proof of Work (adjust difficulty here)
        difficulty = 4
        target = "0" * difficulty

        while not new_block.hash.startswith(target):
            new_block.nonce += 1
            new_block.hash = new_block.calculate_hash()

        return new_block

    def get_product_history(self, product_id):
        # Return all blocks related to the product_id
        return [blk for blk in self.chain if blk.data.get("product_id") == product_id]

# --- P2P Networking Code ---

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
PEERS = []  # Connected peer sockets
blockchain = Blockchain()


def handle_client(conn, addr):
    print(f"Connection from {addr}")
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break
            msg = json.loads(data.decode())
            if msg["type"] == "NEW_BLOCK":
                block_data = msg["data"]
                block = Block.from_dict(block_data)
                if blockchain.add_block(block):
                    print(f"✅ Block added from {addr}: {block.data}")
                    broadcast_block(block, exclude_conn=conn)
                else:
                    print(f"❌ Rejected block from {addr}")
            elif msg["type"] == "REQUEST_CHAIN":
                # Send whole blockchain to peer
                chain_data = [blk.to_dict() for blk in blockchain.chain]
                response = json.dumps({"type": "CHAIN_RESPONSE", "data": chain_data}).encode()
                conn.sendall(response)
            elif msg["type"] == "CHAIN_RESPONSE":
                # Peer sent us their chain, check if longer and valid
                their_chain = [Block.from_dict(d) for d in msg["data"]]
                if len(their_chain) > len(blockchain.chain) and is_valid_chain(their_chain):
                    blockchain.chain = their_chain
                    print(f"🔄 Chain updated from {addr}")
        except Exception as e:
            print(f"Error handling client {addr}: {e}")
            break
    conn.close()
    if conn in PEERS:
        PEERS.remove(conn)
    print(f"Connection closed for {addr}")


def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', PORT))
    s.listen(5)
    print(f"🔊 Listening on port {PORT}")
    while True:
        conn, addr = s.accept()
        PEERS.append(conn)
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


def connect_to_peer(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        PEERS.append(s)
        print(f"🔗 Connected to peer {ip}:{port}")
        # Request chain sync on connection
        request_chain(s)
        threading.Thread(target=handle_client, args=(s, (ip, port)), daemon=True).start()
    except Exception as e:
        print(f"❌ Could not connect to {ip}:{port} — {e}")


def broadcast_block(block, exclude_conn=None):
    msg = {
        "type": "NEW_BLOCK",
        "data": block.to_dict()
    }
    encoded = json.dumps(msg).encode()
    for peer in PEERS:
        if peer != exclude_conn:
            try:
                peer.send(encoded)
            except:
                pass


def request_chain(conn):
    msg = {
        "type": "REQUEST_CHAIN",
        "data": None
    }
    conn.send(json.dumps(msg).encode())


def is_valid_chain(chain):
    if chain[0].hash != blockchain.chain[0].hash:
        print("Genesis block mismatch")
        return False
    for i in range(1, len(chain)):
        if not blockchain.is_valid_new_block(chain[i], chain[i-1]):
            return False
    return True


def mine_and_broadcast(data):
    print("⛏️ Mining new block...")
    new_block = blockchain.mine_block(data)
    blockchain.add_block(new_block)
    broadcast_block(new_block)
    print("✅ Mined and broadcasted block:", new_block.to_dict())


def print_product_history(product_id):
    history = blockchain.get_product_history(product_id)
    if not history:
        print(f"No records found for product ID: {product_id}")
        return
    print(f"History for product {product_id}:")
    for blk in history:
        print(f"  [{blk.index}] {blk.timestamp} - {blk.data['status']} at {blk.data['location']} (hash: {blk.hash[:8]}...)")

# --- Command Line Interface ---

def start_node():
    threading.Thread(target=start_server, daemon=True).start()
    time.sleep(1)
    print(f"Node running on port {PORT}. Commands:")
    print("  connect <ip> <port>        # connect to a peer")
    print("  mine <product_id> <status> <location>   # add supply chain event")
    print("  history <product_id>       # show product history")
    print("  chain                      # show blockchain summary")
    print("  peers                      # show connected peers")
    print("  exit                       # quit node")

    while True:
        cmd = input("> ").strip()
        if cmd.startswith("connect"):
            _, ip, port = cmd.split()
            connect_to_peer(ip, int(port))
        elif cmd.startswith("mine"):
            parts = cmd.split(maxsplit=4)
            if len(parts) < 5:
                print("Usage: mine <product_id> <status> <location>")
                continue
            _, product_id, status, location = parts[:4]
            data = {
                "product_id": product_id,
                "status": status,
                "location": location,
                "timestamp": datetime.utcnow().isoformat()
            }
            mine_and_broadcast(data)
        elif cmd.startswith("history"):
            _, product_id = cmd.split()
            print_product_history(product_id)
        elif cmd == "chain":
            for blk in blockchain.chain:
                print(f"[{blk.index}] {blk.timestamp} - {blk.data['product_id']}: {blk.data['status']} at {blk.data['location']}")
        elif cmd == "peers":
            print(f"Connected peers: {len(PEERS)}")
        elif cmd == "exit":
            print("Exiting node...")
            break
        else:
            print("Unknown command")


if __name__ == "__main__":
    start_node()
