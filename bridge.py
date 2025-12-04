from web3 import Web3
from web3.providers.rpc import HTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware #Necessary for POA chains
from datetime import datetime
import json
import pandas as pd


source_chain = 'avax'
destination_chain = 'bsc'
contract_info = "contract_info.json"
private_key = "5a2ff54fc754cf24fbd227e59f578921628066d4ed7ad21be2c6bfefae6057c6"
account_address = '0x10aff6e7abe9a5b51bd776987d296b0b95db8ee82b3ec9e71ced86a89bea1045'



def connect_to(role):
    """role should be either 'source' or 'destination' """
    if role == "source":  # AVAX C-chain testnet
        api_url = "https://api.avax-test.network/ext/bc/C/rpc"
    elif role == "destination":  # BSC testnet
        api_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"
    else:
        raise ValueError("role must be 'source' or 'destination'")

    w3 = Web3(Web3.HTTPProvider(api_url))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3


def get_contract_info(role, contract_info_file=contract_info):
    """
    Load the contract_info file into a dictionary and return the entry
    for the chain mapped from the role ('source'->'avax', 'destination'->'bsc').
    """
    try:
        with open(contract_info_file, "r") as f:
            contracts = json.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to read contract info file '{contract_info_file}': {e}")

    if role not in ROLE_TO_CHAINKEY:
        raise ValueError(f"role must be 'source' or 'destination', got: {role}")

    chain_key = ROLE_TO_CHAINKEY[role]  # <-- FIX for KeyError: 'source'
    if chain_key not in contracts:
        raise KeyError(
            f"contract_info.json has keys {list(contracts.keys())}, "
            f"but code looked for '{chain_key}' (mapped from role '{role}')."
        )

    return contracts[chain_key]


def scan_blocks(role, contract_info_file=contract_info):
    """
    role - (string) should be either "source" or "destination"
    Scan the last 5 blocks of the source and destination chains
    Look for 'Deposit' events on the source chain and 'Unwrap' events on the destination chain
    When Deposit events are found on the source chain, call the 'wrap' function on the destination chain
    When Unwrap events are found on the destination chain, call the 'withdraw' function on the source chain
    """
    if role not in ["source", "destination"]:
        print(f"Invalid role: {role}")
        return 0

    # Connect to both chains (roles, not 'avax'/'bsc')
    w3_src = connect_to("source")
    w3_dst = connect_to("destination")

    # Load contracts (roles mapped to JSON keys)
    src_info = get_contract_info("source", contract_info_file)
    dst_info = get_contract_info("destination", contract_info_file)

    source_contract_address = Web3.to_checksum_address(src_info["address"])
    destination_contract_address = Web3.to_checksum_address(dst_info["address"])

    source_contract = w3_src.eth.contract(address=source_contract_address, abi=src_info["abi"])
    destination_contract = w3_dst.eth.contract(address=destination_contract_address, abi=dst_info["abi"])

    sender = Web3.to_checksum_address(account_address)

    # last 5 blocks
    src_end_block = w3_src.eth.block_number
    src_start_block = max(0, src_end_block - 5)

    dst_end_block = w3_dst.eth.block_number
    dst_start_block = max(0, dst_end_block - 5)

    arg_filter = {}

    if role == "source":
        # Web3.py uses from_block / to_block (NOT fromBlock/toBlock)
        event_filter = source_contract.events.Deposit.create_filter(
            from_block=src_start_block,
            to_block=src_end_block,
            argument_filters=arg_filter,
        )

        for event in event_filter.get_all_entries():
            txn = destination_contract.functions.wrap(
                event["args"]["token"],
                event["args"]["recipient"],
                event["args"]["amount"],
            ).build_transaction(
                {
                    "from": sender,
                    "chainId": w3_dst.eth.chain_id,
                    "gas": 500000,
                    "nonce": w3_dst.eth.get_transaction_count(sender),
                }
            )
            signed_txn = w3_dst.eth.account.sign_transaction(txn, private_key=private_key)
            tx_hash = w3_dst.eth.send_raw_transaction(signed_txn.rawTransaction)
            print("wrap tx:", tx_hash.hex())

    else:  # role == "destination"
        event_filter = destination_contract.events.Unwrap.create_filter(
            from_block=dst_start_block,
            to_block=dst_end_block,
            argument_filters=arg_filter,
        )

        for event in event_filter.get_all_entries():
            txn = source_contract.functions.withdraw(
                event["args"]["underlying_token"],
                event["args"]["to"],
                event["args"]["amount"],
            ).build_transaction(
                {
                    "from": sender,
                    "chainId": w3_src.eth.chain_id,
                    "gas": 2000000,
                    "nonce": w3_src.eth.get_transaction_count(sender),
                }
            )
            signed_txn = w3_src.eth.account.sign_transaction(txn, private_key=private_key)
            tx_hash = w3_src.eth.send_raw_transaction(signed_txn.rawTransaction)
            print("withdraw tx:", tx_hash.hex())







