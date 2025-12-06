
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from eth_account import Account
from eth_account.messages import encode_defunct
import json
import os

AVAX_RPC = "https://api.avax-test.network/ext/bc/C/rpc"
BSC_RPC  = "https://data-seed-prebsc-1-s1.binance.org:8545/"

contract_info = "contract_info.json"

# Warden credentials (deployer of both bridge contracts)
PRIVATE_KEY = "0x10aff6e7abe9a5b51bd776987d296b0b95db8ee82b3ec9e71ced86a89bea1045"
account_address = '0x12349840E00aD66A7E2038777d58601b9dF11D8d'


def connect_to(chain):
    """
    Connect to the specified blockchain.
    
    Args:
        chain: "source" for Avalanche or "destination" for BNB
        
    Returns:
        Web3 instance connected to the appropriate RPC
    """
    if chain == "source":
        w3 = Web3(Web3.HTTPProvider(AVAX_RPC))
    elif chain == "destination":
        w3 = Web3(Web3.HTTPProvider(BSC_RPC))
    else:
        raise ValueError("chain must be 'source' or 'destination'")
    
    # Add POA middleware
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3


def get_contract_info(chain, contract_info):
    """
    Get contract information for the specified chain.
    
    Args:
        chain: "source" or "destination"
        contract_info: Path to contract_info.json file or dict
        
    Returns:
        Dictionary with contract address and ABI
    """
    # Load contract info if it's a file path
    if isinstance(contract_info, str):
        with open(contract_info, 'r') as f:
            contracts = json.load(f)
    else:
        contracts = contract_info
    
    # Support both formats: autograder (source/destination) and legacy
    if chain in contracts and isinstance(contracts[chain], dict):
        # Autograder format: contracts['source'] = {'address': ..., 'abi': ...}
        return contracts[chain]
    else:
        # Legacy format: contracts['source_contract'], contracts['source_abi']
        if chain == "source":
            return {
                'address': contracts.get('source_contract', ''),
                'abi': contracts.get('source_abi', [])
            }
        elif chain == "destination":
            return {
                'address': contracts.get('destination_contract', ''),
                'abi': contracts.get('destination_abi', [])
            }
    
    raise ValueError(f"Contract info for chain '{chain}' not found")


def sign_message(token, to, amount, nonce):
    """
    Sign a message for cross-chain verification.
    
    Args:
        token: Token address
        to: Recipient address
        amount: Amount to transfer
        nonce: Transaction nonce
        
    Returns:
        Signature bytes
    """
    # Initialize account
    account = Account.from_key(PRIVATE_KEY)
    
    # Create message hash
    message_hash = Web3.solidity_keccak256(
        ['address', 'address', 'uint256', 'uint256'],
        [
            Web3.to_checksum_address(token),
            Web3.to_checksum_address(to),
            amount,
            nonce
        ]
    )
    
    # Sign with Ethereum signed message prefix
    signed_message = account.sign_message(encode_defunct(message_hash))
    return signed_message.signature


def scan_blocks(chain, contract_info="contract_info.json"):
    """
    Scan last 1000 blocks for events and process them.
    
    Args:
        chain: "source" or "destination" - which chain to scan
        contract_info: Path to contract_info.json file (default: "contract_info.json")
        
    Returns:
        Number of events processed
    """
    if chain not in ["source", "destination"]:
        print(f"Invalid chain: {chain}")
        return 0
    
    # Connect to both chains
    w3_src = connect_to("source")
    w3_dst = connect_to("destination")
    
    # Get contract info
    src_info = get_contract_info("source", contract_info)
    dst_info = get_contract_info("destination", contract_info)
    
    # Initialize contracts
    src_contract = w3_src.eth.contract(
        address=Web3.to_checksum_address(src_info["address"]),
        abi=src_info["abi"]
    )
    
    dst_contract = w3_dst.eth.contract(
        address=Web3.to_checksum_address(dst_info["address"]),
        abi=dst_info["abi"]
    )
    
    # Initialize account
    account = Account.from_key(PRIVATE_KEY)
    
    # Track events processed
    events_processed = 0
    
    if chain == "source":
        # Scan for Deposit events on source chain
        print(f"\n=== Scanning Source Chain (Avalanche) ===")
        
        src_end = w3_src.eth.block_number
        src_start = max(0, src_end - 1000)
        
        print(f"Scanning blocks {src_start} to {src_end}")
        
        try:
            deposit_filter = src_contract.events.Deposit.create_filter(
                fromBlock=src_start,
                toBlock=src_end
            )
            
            events = deposit_filter.get_all_entries()
            print(f"Found {len(events)} Deposit events")
            
            for event in events:
                # Extract event data
                token = event['args']['token']
                from_addr = event['args']['from']
                to = event['args']['to']
                amount = event['args']['amount']
                nonce = event['args']['nonce']
                
                print(f"\nDeposit Event #{nonce}:")
                print(f"  Token: {token}")
                print(f"  From: {from_addr}")
                print(f"  To: {to}")
                print(f"  Amount: {amount}")
                
                try:
                    # Sign the message
                    signature = sign_message(token, to, amount, nonce)
                    
                    # Build wrap() transaction on destination
                    tx = dst_contract.functions.wrap(
                        Web3.to_checksum_address(token),
                        Web3.to_checksum_address(to),
                        amount,
                        nonce,
                        signature
                    ).build_transaction({
                        'from': account.address,
                        'nonce': w3_dst.eth.get_transaction_count(account.address),
                        'gas': 500000,
                        'gasPrice': w3_dst.eth.gas_price,
                    })
                    
                    # Sign and send transaction
                    signed_tx = account.sign_transaction(tx)
                    tx_hash = w3_dst.eth.send_raw_transaction(signed_tx.rawTransaction)
                    
                    print(f"  Wrap tx: {tx_hash.hex()}")
                    
                    # Wait for confirmation
                    receipt = w3_dst.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                    if receipt['status'] == 1:
                        print(f"  ✓ Wrap successful!")
                        events_processed += 1
                    else:
                        print(f"  ✗ Wrap failed!")
                        
                except Exception as e:
                    print(f"  ✗ Error: {e}")
                    
        except Exception as e:
            print(f"Error scanning deposits: {e}")
    
    else:  # chain == "destination"
        # Scan for Unwrap events on destination chain
        print(f"\n=== Scanning Destination Chain (BNB) ===")
        
        dst_end = w3_dst.eth.block_number
        dst_start = max(0, dst_end - 1000)
        
        print(f"Scanning blocks {dst_start} to {dst_end}")
        
        try:
            unwrap_filter = dst_contract.events.Unwrap.create_filter(
                fromBlock=dst_start,
                toBlock=dst_end
            )
            
            events = unwrap_filter.get_all_entries()
            print(f"Found {len(events)} Unwrap events")
            
            for event in events:
                # Extract event data
                wrapped_token = event['args']['wrappedToken']
                source_token = event['args']['sourceToken']
                from_addr = event['args']['from']
                to = event['args']['to']
                amount = event['args']['amount']
                nonce = event['args']['nonce']
                
                print(f"\nUnwrap Event #{nonce}:")
                print(f"  Wrapped Token: {wrapped_token}")
                print(f"  Source Token: {source_token}")
                print(f"  From: {from_addr}")
                print(f"  To: {to}")
                print(f"  Amount: {amount}")
                
                try:
                    # Sign the message (using source token)
                    signature = sign_message(source_token, to, amount, nonce)
                    
                    # Build withdraw() transaction on source
                    tx = src_contract.functions.withdraw(
                        Web3.to_checksum_address(source_token),
                        Web3.to_checksum_address(to),
                        amount,
                        nonce,
                        signature
                    ).build_transaction({
                        'from': account.address,
                        'nonce': w3_src.eth.get_transaction_count(account.address),
                        'gas': 500000,
                        'gasPrice': w3_src.eth.gas_price,
                    })
                    
                    # Sign and send transaction
                    signed_tx = account.sign_transaction(tx)
                    tx_hash = w3_src.eth.send_raw_transaction(signed_tx.rawTransaction)
                    
                    print(f"  Withdraw tx: {tx_hash.hex()}")
                    
                    # Wait for confirmation
                    receipt = w3_src.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                    if receipt['status'] == 1:
                        print(f"  ✓ Withdraw successful!")
                        events_processed += 1
                    else:
                        print(f"  ✗ Withdraw failed!")
                        
                except Exception as e:
                    print(f"  ✗ Error: {e}")
                    
        except Exception as e:
            print(f"Error scanning unwraps: {e}")
    
    return events_processed


if __name__ == "__main__":
    # Main execution
    print("=" * 70)
    print("CROSS-CHAIN BRIDGE - EVENT PROCESSOR")
    print("=" * 70)
    
    # Process both chains
    total_processed = 0
    total_processed += scan_blocks("source")
    total_processed += scan_blocks("destination")
    
    print("\n" + "=" * 70)
    print(f"Bridge processing complete! Processed {total_processed} events")
    print("=" * 70)




