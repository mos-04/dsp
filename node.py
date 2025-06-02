import socket
import threading
import json
import sys
from blockchain import Blockchain, Block
import time

PORT = int(sys.argv[1])  # Get port from CLI
PEERS = []  # Active peer connections

blockchain = Blockchain()

# ------------------ Server ------------------
def handle_client(conn, addr):
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break
            msg = json.loads(data.decode())
            if msg["type"] == "NEW_BLOCK":
                block_data = msg["data"]
                block = Block(**block_data)
                if blockchain.add_block(block):
                    print(f"✅ Block added from {addr}")
                    broadcast_block(block)
                else:
                    print(f"❌ Rejected block from {addr}")
        except:
            break
    conn.close()

def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', PORT))
    s.listen(5)
    print(f"🔊 Listening on port {PORT}")
    while True:
        conn, addr = s.accept()
        PEERS.append(conn)
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

# ------------------ Client ------------------
def connect_to_peer(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        PEERS.append(s)
        print(f"🔗 Connected to peer {ip}:{port}")
    except Exception as e:
        print(f"❌ Could not connect to {ip}:{port} — {e}")

def broadcast_block(block):
    msg = {
        "type": "NEW_BLOCK",
        "data": block.__dict__
    }
    encoded = json.dumps(msg).encode()
    for peer in PEERS:
        try:
            peer.send(encoded)
        except:
            pass

def mine_and_broadcast(data):
    print("⛏️  Mining new block...")
    new_block = blockchain.mine_block(data)
    blockchain.add_block(new_block)
    broadcast_block(new_block)
    print("✅ Mined and broadcasted block:", new_block.__dict__)

# ------------------ Startup ------------------
def start_node():
    threading.Thread(target=start_server, daemon=True).start()
    time.sleep(1)
    print("Node ready. Commands:\n1. connect IP PORT\n2. mine DATA\n3. chain\n")

    while True:
        cmd = input("> ")
        if cmd.startswith("connect"):
            _, ip, port = cmd.strip().split()
            connect_to_peer(ip, int(port))
        elif cmd.startswith("mine"):
            _, *data = cmd.strip().split()
            mine_and_broadcast(" ".join(data))
        elif cmd == "chain":
            for blk in blockchain.chain:
                print(f"[{blk.index}] {blk.hash[:8]}... -> {blk.previous_hash[:8]}...")
        else:
            print("Commands:\n1. connect IP PORT\n2. mine DATA\n3. chain")

if __name__ == "__main__":
    start_node()
