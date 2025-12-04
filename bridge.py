from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
import json

AVAX_RPC = "https://api.avax-test.network/ext/bc/C/rpc"
BSC_RPC  = "https://data-seed-prebsc-1-s1.binance.org:8545/"

contract_info = "contract_info.json"

# Warden credentials (deployer of both bridge contracts)
private_key = "<YOUR_WARDEN_PRIVATE_KEY>".removeprefix("0x")
account_address = Web3.to_checksum_address("<YOUR_WARDEN_ADDRESS>")


def connect_to(chain):
    # chain is "source" or "destination"
    if chain == "source":
        w3 = Web3(Web3.HTTPProvider(AVAX_RPC))
    elif chain == "destination":
        w3 = Web3(Web3.HTTPProvider(BSC_RPC))
    else:
        raise ValueError("chain must be 'source' or 'destination'")

    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3


def get_contract_info(chain, contract_info_file=contract_info):
    with open(contract_info_file, "r") as f:
        contracts = json.load(f)
    return contracts[chain]  # expects "source" and "destination"


def scan_blocks(chain, contract_info_file=contract_info):
    """
    chain: "source" or "destination"
    Scan last 5 blocks, react to events:
      - Deposit on source => wrap on destination
      - Unwrap on destination => withdraw on source
    """
    if chain not in ["source", "destination"]:
        print(f"Invalid chain: {chain}")
        return 0

    w3_src = connect_to("source")
    w3_dst = connect_to("destination")

    src_info = get_contract_info("source", contract_info_file)
    dst_info = get_contract_info("destination", contract_info_file)

    src_contract = w3_src.eth.contract(
        address=Web3.to_checksum_address(src_info["address"]),
        abi=src_info["abi"],
    )
    dst_contract = w3_dst.eth.contract(
        address=Web3.to_checksum_address(dst_info["address"]),
        abi=dst_info["abi"],
    )

    # last 5 blocks
    src_end = w3_src.eth.block_number
    src_start = max(0, src_end - 5)

    dst_end = w3_dst.eth.block_number
    dst_start = max(0, dst_end - 5)

    if chain == "source":
        f = src_contract.events.Deposit.create_filter(
            from_block=src_start,
            to_block=src_end,
            argument_filters={},
        )
        for evt in f.get_all_entries():
            # Build wrap() on destination
            tx = dst_contract.functions.wrap(
                evt["args"]["token"],
                evt["args"]["recipient"],
                evt["args"]["amount"],
            ).build_transaction({
                "from": account_address,
                "chainId": w3_dst.eth.chain_id,
                "gas": 500000,
                "nonce": w3_dst.eth.get_transaction_count(account_address),
            })

            signed = w3_dst.eth.account.sign_transaction(tx, private_key=private_key)
            txh = w3_dst.eth.send_raw_transaction(signed.rawTransaction)
            print("wrap:", txh.hex())

    else:  # chain == "destination"
        f = dst_contract.events.Unwrap.create_filter(
            from_block=dst_start,
            to_block=dst_end,
            argument_filters={},
        )
        for evt in f.get_all_entries():
            # Build withdraw() on source
            tx = src_contract.functions.withdraw(
                evt["args"]["underlying_token"],
                evt["args"]["to"],
                evt["args"]["amount"],
            ).build_transaction({
                "from": account_address,
                "chainId": w3_src.eth.chain_id,
                "gas": 2000000,
                "nonce": w3_src.eth.get_transaction_count(account_address),
            })

            signed = w3_src.eth.account.sign_transaction(tx, private_key=private_key)
            txh = w3_src.eth.send_raw_transaction(signed.rawTransaction)
            print("withdraw:", txh.hex())





