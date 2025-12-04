from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware  # Necessary for POA chains
import json

source_chain = "avax"
destination_chain = "bsc"
contract_info = "contract_info.json"

# NOTE: In many setups this should be WITHOUT the 0x prefix; this line makes it safe either way.
private_key = "0x10aff6e7abe9a5b51bd776987d296b0b95db8ee82b3ec9e71ced86a89bea1045"
private_key = private_key.removeprefix("0x")

account_address = "0x12349840E00aD66A7E2038777d58601b9dF11D8d"


def connect_to(chain):
    """
    chain: 'source' or 'destination' (per the assignment/autograder)
    """
    if chain == "source":  # AVAX C-chain testnet
        api_url = "https://api.avax-test.network/ext/bc/C/rpc"
    elif chain == "destination":  # BSC testnet
        api_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"
    else:
        raise ValueError("chain must be 'source' or 'destination'")

    w3 = Web3(Web3.HTTPProvider(api_url))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3


def get_contract_info(chain, contract_info_file=contract_info):
    """
    Load the contract_info file into a dictionary and return contracts[chain].

    IMPORTANT: Autograder expects top-level keys in contract_info.json:
      - "source"
      - "destination"
    """
    try:
        with open(contract_info_file, "r") as f:
            contracts = json.load(f)
    except Exception as e:
        print(f"Failed to read contract info\nPlease contact your instructor\n{e}")
        return 0

    return contracts[chain]


def scan_blocks(chain, contract_info_file=contract_info):
    """
    chain - (string) should be either "source" or "destination"
    Scan the last 5 blocks of the source and destination chains
    Look for 'Deposit' events on the source chain and 'Unwrap' events on the destination chain
    When Deposit events are found on the source chain, call the 'wrap' function the destination chain
    When Unwrap events are found on the destination chain, call the 'withdraw' function on the source chain
    """
    if chain not in ["source", "destination"]:
        print(f"Invalid chain: {chain}")
        return 0

    # Connect to both chains
    w3_src = connect_to("source")
    w3_dst = connect_to("destination")

    # Load deployed contract info (expects contract_info.json has keys source/destination)
    src_info = get_contract_info("source", contract_info_file)
    dst_info = get_contract_info("destination", contract_info_file)

    source_contract_address = Web3.to_checksum_address(src_info["address"])
    destination_contract_address = Web3.to_checksum_address(dst_info["address"])

    source_contract = w3_src.eth.contract(address=source_contract_address, abi=src_info["abi"])
    destination_contract = w3_dst.eth.contract(address=destination_contract_address, abi=dst_info["abi"])

    sender = Web3.to_checksum_address(account_address)

    # Last 5 blocks on each chain
    src_end_block = w3_src.eth.block_number
    src_start_block = max(0, src_end_block - 5)

    dst_end_block = w3_dst.eth.block_number
    dst_start_block = max(0, dst_end_block - 5)

    arg_filter = {}

    if chain == "source":
        # Web3.py uses from_block / to_block
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

    else:  # chain == "destination"
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







