import hashlib
from datetime import datetime


class Block:
    def __init__(self, index, proof_number, previous_block_hash, meta_data):
        """
        this for the creation of a new block NOT for the blockchain
        :param index: this keeps track of the position of the block within the blockchain;
        :param proof_number: this is the number produced during the creation of a new block;
        :param previous_block_hash: this refers to the hash of the previous block within the chain;
        :param meta_data: this refers to whatever information we want to put in. can give json format or just str.
        """
        self.index = index
        self.proof_number = proof_number
        self.previous_block_hash = str(previous_block_hash)
        self.meta_data = meta_data
        self.timestamp = str(datetime.now())
        self.block_data = "-".join(meta_data) + "-" + self.timestamp \
                          + "-" + self.previous_block_hash
        self.block_hash = hashlib.sha256(self.block_data.encode()).hexdigest()


class BlockChain:
    def __init__(self):
        """
        creation of the blockchain. Need to be initiated or read from a previous stored blockchain(file)
        """
        self.chain = []
        self.current_data = []
        self.nodes = set()

    def construct_block(self, data, proof_number=0, previous_block_hash=0):
        """
        :param data: information to stored.
        :param proof_number: taken from previous number unless it is the first
        :param previous_block_hash:  taken from previous block unless it is the first then it will be 0
        :return:
        """
        block = Block(
            index=len(self.chain),
            proof_number=proof_number,
            previous_block_hash=previous_block_hash,
            meta_data=data)

        self.chain.append(block)
        return block


atest = BlockChain()
BlockChain.construct_block(atest, "filename:test, filehash:123456")

print("output")
print(atest.chain[0].block_hash)
"""
f = open("test.txt", "w")
f.write(atest)
f.close()

"""
