import hashlib
import os
import random


def mine_block(k, prev_hash, transactions):
    """
        k - Number of trailing zeros in the binary representation (integer)
        prev_hash - the hash of the previous block (bytes)
        rand_lines - a set of "transactions," i.e., data to be included in this block (list of strings)

        Complete this function to find a nonce such that 
        sha256( prev_hash + rand_lines + nonce )
        has k trailing zeros in its *binary* representation
    """
    if not isinstance(k, int) or k < 0:
        print("mine_block expects positive integer")
        return b'\x00'

    #  your code to find a nonce here
    nonce_value = 0
    
    while True:
        # Convert nonce to bytes
        nonce = str(nonce_value).encode('utf-8')
        
        # Create hash object
        m = hashlib.sha256()
        
        # Add prev_hash
        m.update(prev_hash)
        
        # Add all transactions in order
        for line in rand_lines:
            m.update(line.encode('utf-8'))
        
        # Add nonce
        m.update(nonce)
        
        # Get the hash
        block_hash = m.digest()
        
        # Convert hash to binary and check trailing zeros
        hash_int = int.from_bytes(block_hash, byteorder='big')
        hash_bin = bin(hash_int)[2:]
        
        # Count trailing zeros
        trailing_zeros = 0
        for i in range(len(hash_bin) - 1, -1, -1):
            if hash_bin[i] == '0':
                trailing_zeros += 1
            else:
                break
        
        # Check if we have enough trailing zeros
        if trailing_zeros >= k:
            assert isinstance(nonce, bytes), 'nonce should be of type bytes'
            return nonce
        
        nonce_value += 1
    #assert isinstance(nonce, bytes), 'nonce should be of type bytes'
    #return nonce


def get_random_lines(filename, quantity):
    """
    This is a helper function to get the quantity of lines ("transactions")
    as a list from the filename given. 
    Do not modify this function
    """
    lines = []
    with open(filename, 'r') as f:
        for line in f:
            lines.append(line.strip())

    random_lines = []
    for x in range(quantity):
        random_lines.append(lines[random.randint(0, quantity - 1)])
    return random_lines


if __name__ == '__main__':
    # This code will be helpful for your testing
    filename = "bitcoin_text.txt"
    num_lines = 10  # The number of "transactions" included in the block

    # The "difficulty" level. For our blocks this is the number of Least Significant Bits
    # that are 0s. For example, if diff = 5 then the last 5 bits of a valid block hash would be zeros
    # The grader will not exceed 20 bits of "difficulty" because larger values take to long
    diff = 5

    prev_hash = hashlib.sha256(b"previous_block").digest()
    
    # Get random lines
    rand_lines = get_random_lines(filename, num_lines)
    
    # Call mine_block with all 3 parameters
    nonce = mine_block(diff, prev_hash, rand_lines)
    print(f"Found nonce: {nonce}")

    #transactions = get_random_lines(filename, num_lines)
    #nonce = mine_block(diff, transactions)
    #print(nonce)
