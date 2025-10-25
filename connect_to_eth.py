import json
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from web3.providers.rpc import HTTPProvider

'''
If you use one of the suggested infrastructure providers, the url will be of the form
now_url  = f"https://eth.nownodes.io/{now_token}"
alchemy_url = f"https://eth-mainnet.alchemyapi.io/v2/{alchemy_token}"
infura_url = f"https://mainnet.infura.io/v3/{infura_token}"
'''

def connect_to_eth():
	infura_token = "14beb6ddda7844cc8a4c4b0a00f4350a"
  url = f"https://mainnet.infura.io/v3/{infura_token}"
 
	w3 = Web3(HTTPProvider(url))
	assert w3.is_connected(), f"Failed to connect to provider at {url}"
	return w3


def connect_with_middleware(contract_json):
	with open(contract_json, "r") as f:
		d = json.load(f)
		d = d['bsc']
		address = d['address']
		abi = d['abi']
  

	bsc_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"
	# The first section will be the same as "connect_to_eth()" but with a BNB url
	w3 = Web3(HTTPProvider(bsc_url))
  assert w3.is_connected(), f"Failed to connect to BSC provider at {bsc_url}"
  w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

  checksum_address = Web3.to_checksum_address(address)
  contract = w3.eth.contract(address=checksum_address, abi=abi)
    

	# The second section requires you to inject middleware into your w3 object and
	# create a contract object. Read more on the docs pages at https://web3py.readthedocs.io/en/stable/middleware.html
	# and https://web3py.readthedocs.io/en/stable/web3.contract.html
	

	return w3, contract


if __name__ == "__main__":
	
      # Test Ethereum mainnet connection
    print("=" * 50)
    print("Testing Ethereum Mainnet Connection")
    print("=" * 50)
    
    w3_eth = connect_to_eth()
    print(f"✓ Connected to Ethereum: {w3_eth.is_connected()}")
    print(f"✓ Chain ID: {w3_eth.eth.chain_id}")
    
    # Get latest block information
    latest_block = w3_eth.eth.get_block('latest')
    print(f"✓ Latest block number: {latest_block['number']}")
    print(f"✓ Latest block timestamp: {latest_block['timestamp']}")
    
    print()
    
    # Test BNB testnet connection
    print("=" * 50)
    print("Testing BNB Testnet Connection")
    print("=" * 50)
    
    w3_bnb, contract_bnb = connect_with_middleware("contract_info.json")
    print(f"✓ Connected to BNB testnet: {w3_bnb.is_connected()}")
    print(f"✓ Chain ID: {w3_bnb.eth.chain_id}")
    print(f"✓ Contract address: {contract_bnb.address}")
    print(f"✓ Contract has {len(contract_bnb.abi)} functions/events defined")
    
    # Optional: Try to read merkleRoot from contract
    try:
        merkle_root = contract_bnb.functions.merkleRoot().call()
        print(f"✓ Contract merkleRoot: {merkle_root.hex()}")
    except Exception as e:
        print(f"Note: Could not read merkleRoot (this is normal if not set yet)")
    
    print()
    print("=" * 50)
    print("All connections successful! ✓")
    print("=" * 50)