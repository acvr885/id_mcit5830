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



def connect_to(chain):
    if chain == 'source':  # The source contract chain is avax
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc" #AVAX C-chain testnet

    if chain == 'destination':  # The destination contract chain is bsc
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/" #BSC testnet

    if chain in ['source','destination']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3


def get_contract_info(chain, contract_info):
    """
        Load the contract_info file into a dictionary
        This function is used by the autograder and will likely be useful to you
    """
    try:
        with open(contract_info, 'r')  as f:
            contracts = json.load(f)
    except Exception as e:
        print( f"Failed to read contract info\nPlease contact your instructor\n{e}" )
        return 0
    return contracts[chain]



def scan_blocks(chain, contract_info="contract_info.json"):
    """
        chain - (string) should be either "source" or "destination"
        Scan the last 5 blocks of the source and destination chains
        Look for 'Deposit' events on the source chain and 'Unwrap' events on the destination chain
        When Deposit events are found on the source chain, call the 'wrap' function the destination chain
        When Unwrap events are found on the destination chain, call the 'withdraw' function on the source chain
    """

    # This is different from Bridge IV where chain was "avax" or "bsc"
    if chain not in ['source','destination']:
        print( f"Invalid chain: {chain}" )
        return 0
    
    w3_src = connect_To(source_chain)
    w3_dst = connect_To(destination_chain)
    source_contracts = get_contract_info("source")
    destination_contracts = get_contract_info("destination")
    source_contract_address, src_abi = source_contracts["address"], source_contracts["abi"]
    destination_contract_address, dst_abi = destination_contracts["address"], destination_contracts["abi"]
    
    source_contract = w3_src.eth.contract(address=source_contract_address, abi=src_abi)
    destination_contract = w3_dst.eth.contract(address=destination_contract_address, abi=dst_abi)

    
    src_end_block = w3_src.eth.get_block_number()
    src_start_block = src_end_block - 5
    dst_end_block = w3_dst.eth.get_block_number()
    dst_start_block = dst_end_block - 5

    arg_filter = {}
    if chain == "source":  #Source
        
        event_filter = source_contract.events.Deposit.create_filter(fromBlock=src_start_block, toBlock = src_end_block, argument_filters=arg_filter)
        for event in event_filter.get_all_entries():
            txn = destination_contract.functions.wrap(event.args['token'], event.args['recipient'], event.args['amount']).build_transaction({
                'from': account_address,
                'chainId': w3_dst.eth.chain_id,
                'gas': 500000,
                'nonce': w3_dst.eth.get_transaction_count(account_address)
            })
            signed_txn = w3_dst.eth.account.sign_transaction(txn, private_key=private_key)
            w3_dst.eth.send_raw_transaction(signed_txn.rawTransaction)

    elif chain == "destination":  #Destination
        
        event_filter = destination_contract.events.Unwrap.create_filter(fromBlock=dst_start_block, toBlock = dst_end_block, argument_filters=arg_filter)
        for event in event_filter.get_all_entries():
            txn = source_contract.functions.withdraw(event.args['underlying_token'], event.args['to'], event.args['amount']).build_transaction({
            'from': account_address,
            'chainId': w3_src.eth.chain_id,
            'gas': 2000000,
            'nonce': w3_src.eth.get_transaction_count(account_address)
            })
            signed_txn = w3_src.eth.account.sign_transaction(txn, private_key=private_key)
            w3_src.eth.send_raw_transaction(signed_txn.rawTransaction)
