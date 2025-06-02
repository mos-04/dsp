import hashlib
import time
import json

class Block:
    def __init__(self, index, previous_hash, timestamp, data, nonce=0):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.data = data
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        value = f"{self.index}{self.previous_hash}{self.timestamp}{self.data}{self.nonce}"
        return hashlib.sha256(value.encode()).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.difficulty = 4

    def create_genesis_block(self):
        return Block(0, "0", time.time(), "Genesis Block")

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, block):
        if self.is_valid_new_block(block, self.get_latest_block()):
            self.chain.append(block)
            return True
        return False

    def is_valid_new_block(self, block, previous_block):
        if block.index != previous_block.index + 1:
            return False
        if block.previous_hash != previous_block.hash:
            return False
        if block.calculate_hash() != block.hash:
            return False
        if not block.hash.startswith('0' * self.difficulty):
            return False
        return True

    def mine_block(self, data):
        last_block = self.get_latest_block()
        index = last_block.index + 1
        nonce = 0
        timestamp = time.time()
        while True:
            new_block = Block(index, last_block.hash, timestamp, data, nonce)
            if new_block.hash.startswith('0' * self.difficulty):
                return new_block
            nonce += 1
