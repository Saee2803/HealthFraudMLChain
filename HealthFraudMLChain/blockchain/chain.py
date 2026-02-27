import hashlib
import json
import time

# The blockchain itself (a list of blocks)
blockchain = []

# Function to create a block
def create_block(index, timestamp, data, previous_hash):
    block = {
        'index': index,
        'timestamp': timestamp,
        'data': data,
        'previous_hash': previous_hash,
    }
    block['hash'] = calculate_hash(block)
    return block

# Function to calculate hash of a block
def calculate_hash(block):
    block_string = json.dumps(block, sort_keys=True).encode()
    return hashlib.sha256(block_string).hexdigest()

# Function to get the last block in the chain
def get_last_block():
    return blockchain[-1] if blockchain else None

# Function to add data to the blockchain
def add_to_blockchain(data):
    last_block = get_last_block()
    index = last_block['index'] + 1 if last_block else 0
    timestamp = time.time()
    previous_hash = last_block['hash'] if last_block else '0'

    new_block = create_block(index, timestamp, data, previous_hash)
    blockchain.append(new_block)
    print(f"✅ Block added to blockchain: {new_block}")
    return new_block
