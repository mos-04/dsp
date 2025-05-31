import socket
import threading
import json
import sys
import time
from blockchain import Blockchain, Block

# Read config file dynamically based on argument
if len(sys.argv) != 2:
    print("Usage: python node.py <port>")
    sys.exit(1)

port_arg = sys.argv[1]
with open(f'config_{port_arg}.json') as f:
    config = json.load(f)

PORT = config["port"]
PEERS = config["peers"]

blockchain = Blockchain()
peer_sockets = []

# Handle incoming connections
def handle_client(conn, addr):
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break
            block_data = json.loads(data.decode())
            received_block = Block(**block_data)
            blockchain.add_block(received_block)
            print(f"\n✅ Block added from {addr}")
        except Exception as e:
            print(f"❌ Error from {addr}: {e}")
            break
    conn.close()

# Start server to accept connections
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', PORT))
    server.listen(5)
    print(f"🚀 Node listening on port {PORT}")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

# Connect to peers listed in config
def connect_to_peers():
    for peer in PEERS:
        ip, port = peer.split(":")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, int(port)))
            peer_sockets.append(s)
            print(f"🔗 Connected to peer: {peer}")
        except Exception as e:
            print(f"❌ Failed to connect to {peer}: {e}")

# Broadcast a block to all connected peers
def broadcast_block(block):
    data = json.dumps(block.__dict__).encode()
    for peer in peer_sockets:
        try:
            peer.send(data)
        except Exception as e:
            print(f"⚠️ Error sending to peer: {e}")

# Manually create and broadcast a block
def create_and_broadcast_block():
    data = input("\n📥 Enter data for new block: ")
    new_block = Block(
        index=len(blockchain.chain),
        previous_hash=blockchain.get_latest_block().hash,
        timestamp=time.time(),
        data=data
    )
    blockchain.add_block(new_block)
    broadcast_block(new_block)
    print(f"📤 Block broadcasted: {new_block.hash}")

# Start server thread and connect to peers
threading.Thread(target=start_server, daemon=True).start()
connect_to_peers()

# Main loop to manually add blocks
while True:
    cmd = input("\nType 'add' to create a new block or 'chain' to view blockchain: ").strip().lower()
    if cmd == 'add':
        create_and_broadcast_block()
    elif cmd == 'chain':
        print("\n📦 Current Blockchain:")
        for block in blockchain.chain:
            print(f" - Block {block.index} | Hash: {block.hash[:10]}... | Data: {block.data}")
    else:
        print("Unknown command.")
