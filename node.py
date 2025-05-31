import socket
import threading
import json
from blockchain import Blockchain, Block
import time

blockchain = Blockchain()
PORT = 5000
PEERS = []

def handle_client(conn, addr):
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break
            block_data = json.loads(data.decode())
            new_block = Block(**block_data)
            blockchain.add_block(new_block)
            print(f"Block added from {addr}")
        except:
            break
    conn.close()

def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', PORT))
    s.listen(5)
    print(f"Listening on port {PORT}...")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

def connect_to_peer(ip):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, PORT))
    PEERS.append(s)
    return s

def broadcast_block(block):
    data = json.dumps(block.__dict__).encode()
    for peer in PEERS:
        peer.send(data)

def create_and_broadcast_block(data):
    new_block = Block(len(blockchain.chain), blockchain.get_latest_block().hash, time.time(), data)
    blockchain.add_block(new_block)
    broadcast_block(new_block)

# Start server in a thread
threading.Thread(target=start_server).start()

# Connect to other peers manually (example)
# peer_conn = connect_to_peer('127.0.0.1')
