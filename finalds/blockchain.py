import hashlib
import time

class Block:
    def __init__(self, index, previous_hash, timestamp, data, nonce=0, hash_value=""):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.data = data
        self.nonce = nonce
        self.hash = hash_value or self.calculate_hash()

    def calculate_hash(self):
        value = f"{self.index}{self.previous_hash}{self.timestamp}{self.data}{self.nonce}"
        return hashlib.sha256(value.encode()).hexdigest()

    def mine_block(self, difficulty):
        prefix_str = '0' * difficulty
        while not self.hash.startswith(prefix_str):
            self.nonce += 1
            self.hash = self.calculate_hash()
        print(f"Block mined: {self.hash}")

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.difficulty = 4

    def create_genesis_block(self):
        return Block(0, "0", time.time(), "Genesis Block")

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, new_block):
        new_block.previous_hash = self.get_latest_block().hash
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            if current.hash != current.calculate_hash():
                print("Invalid hash at block", i)
                return False
            if current.previous_hash != previous.hash:
                print("Invalid previous hash at block", i)
                return False
            if not current.hash.startswith('0' * self.difficulty):
                print("Block not mined properly at block", i)
                return False
        return True
