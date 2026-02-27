"""
Minimal blockchain implementation for HealthFraudMLChain
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

class Block:
    def __init__(self, index: int, data: Dict[Any, Any], previous_hash: str):
        self.index = index
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of the block"""
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class Blockchain:
    def __init__(self, db=None, collection_name="blockchain_blocks"):
        self.chain: List[Block] = []
        self.db = db
        self.collection_name = collection_name
        
    def create_genesis_block(self) -> Block:
        """Create the first block in the chain"""
        return Block(0, {"message": "Genesis Block"}, "0")
    
    def get_latest_block(self) -> Block:
        """Get the most recent block"""
        return self.chain[-1] if self.chain else self.create_genesis_block()
    
    def add_block(self, data: Dict[Any, Any], actor_role: str = "system") -> bool:
        """Add a new block to the chain"""
        try:
            if not self.chain:
                self.chain.append(self.create_genesis_block())
            
            previous_block = self.get_latest_block()
            new_block = Block(
                index=len(self.chain),
                data=data,
                previous_hash=previous_block.hash
            )
            self.chain.append(new_block)
            
            # Save to MongoDB if available
            # FIX: PyMongo Database objects do not implement truth value testing.
            # Must use explicit 'is not None' comparison instead of 'if self.db'.
            if self.db is not None and self.collection_name:
            
                self.save_to_mongodb()
            
            return True
        except Exception as e:
            print(f"Error adding block: {e}")
            return False
    
    def is_chain_valid(self) -> bool:
        """Validate the entire blockchain"""
        if not self.chain:
            return True
            
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # Check if current block's hash is valid
            if current_block.hash != current_block.calculate_hash():
                return False
            
            # Check if current block points to previous block
            if current_block.previous_hash != previous_block.hash:
                return False
        
        return True
    
    def get_block_count(self) -> int:
        """Get the number of blocks in the chain"""
        return len(self.chain)
    
    def load_from_mongodb(self):
        """Load blockchain from MongoDB"""

        if self.db is None or self.collection_name is None:

            # Create genesis block if no database
            if not self.chain:
                self.chain.append(self.create_genesis_block())
            return
        
        try:
            collection = self.db[self.collection_name]
            blocks_data = list(collection.find().sort("index", 1))
            
            if not blocks_data:
                # Create genesis block
                self.chain.append(self.create_genesis_block())
                self.save_to_mongodb()
            else:
                # Reconstruct chain from database
                self.chain = []
                for block_data in blocks_data:
                    try:
                        # FIX: Handle legacy blocks that may be missing fields
                        # Use .get() with defaults to avoid KeyError on missing fields
                        block = Block(
                            index=block_data.get("index", len(self.chain)),
                            data=block_data.get("data", {}),  # Default to empty dict if missing
                            previous_hash=block_data.get("previous_hash", "0")
                        )
                        block.timestamp = block_data.get("timestamp", datetime.now(timezone.utc).isoformat())
                        block.hash = block_data.get("hash", block.calculate_hash())
                        self.chain.append(block)
                    except Exception as block_error:
                        # Skip invalid blocks but log warning
                        print(f"Warning: Skipping invalid block during load: {block_error}")
                        continue
                
                # Ensure at least genesis block exists
                if not self.chain:
                    self.chain.append(self.create_genesis_block())
                    
        except Exception as e:
            print(f"Error loading from MongoDB: {e}")
            if not self.chain:
                self.chain.append(self.create_genesis_block())
    
    def save_to_mongodb(self):
        """Save blockchain to MongoDB"""
        # FIX: PyMongo Database objects do not implement truth value testing.
        # Must use explicit 'is None' comparison instead of 'not self.db'.
        if self.db is None or not self.collection_name:
            return
        
        try:
            collection = self.db[self.collection_name]
            # Clear existing data
            collection.delete_many({})
            
            # Save all blocks
            for block in self.chain:
                block_data = {
                    "index": block.index,
                    "timestamp": block.timestamp,
                    "data": block.data,
                    "previous_hash": block.previous_hash,
                    "hash": block.hash
                }
                collection.insert_one(block_data)
        except Exception as e:
            print(f"Error saving to MongoDB: {e}")
    
    def get_chain_as_dict(self) -> List[Dict]:
        """Get blockchain as list of dictionaries"""
        return [{
            "index": block.index,
            "timestamp": block.timestamp,
            "data": block.data,
            "previous_hash": block.previous_hash,
            "hash": block.hash
        } for block in self.chain]