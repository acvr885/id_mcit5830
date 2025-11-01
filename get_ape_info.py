from web3 import Web3
from web3.providers.rpc import HTTPProvider
import requests
import json

bayc_address = "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D"
contract_address = Web3.to_checksum_address(bayc_address)

# You will need the ABI to connect to the contract
# The file 'abi.json' has the ABI for the bored ape contract
# In general, you can get contract ABIs from etherscan
# https://api.etherscan.io/api?module=contract&action=getabi&address=0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D
with open('ape_abi.json', 'r') as f:
    abi = json.load(f)

############################
# Connect to an Ethereum node
api_url = "https://mainnet.infura.io/v3/14beb6ddda7844cc8a4c4b0a00f4350a"  # YOU WILL NEED TO PROVIDE THE URL OF AN ETHEREUM NODE
provider = HTTPProvider(api_url)
web3 = Web3(provider)


def get_ape_info(ape_id):
    assert isinstance(ape_id, int), f"{ape_id} is not an int"
    assert 0 <= ape_id, f"{ape_id} must be at least 0"
    assert 9999 >= ape_id, f"{ape_id} must be less than 10,000"

    data = {'owner': "", 'image': "", 'eyes': ""}

    contract = web3.eth.contract(address=contract_address, abi=abi)
    
    # Step 1: Get the owner of the ape using ownerOf function
    owner = contract.functions.ownerOf(ape_id).call()
    data['owner'] = owner
    
    # Step 2: Get the token URI (IPFS metadata location)
    token_uri = contract.functions.tokenURI(ape_id).call()
    
    # Step 3: Fetch metadata from IPFS
    # token_uri format: ipfs://QmeSjSinHpPnmXmspMjwiXyN6zS4E9zccariGR3jxcaWtq/1
    # Extract the IPFS hash/path
    ipfs_path = token_uri.replace("ipfs://", "")
    
    # Try multiple IPFS gateways for reliability
    gateways = [
        f"https://gateway.pinata.cloud/ipfs/{ipfs_path}",
        f"https://ipfs.io/ipfs/{ipfs_path}"
    ]
    
    metadata = None
    for gateway_url in gateways:
        try:
            response = requests.get(gateway_url, timeout=10)
            if response.status_code == 200:
                metadata = response.json()
                break
        except:
            continue
    
    # If standard gateways fail, try Infura POST method
    if metadata is None:
        try:
            infura_url = f"https://ipfs.infura.io:5001/api/v0/cat?arg={ipfs_path}"
            response = requests.post(infura_url, timeout=10)
            if response.status_code == 200:
                metadata = response.json()
        except:
            pass
    
    # Step 4: Extract image URI from metadata
    if metadata:
        data['image'] = metadata.get('image', '')
        
        # Step 5: Extract eyes attribute from metadata
        attributes = metadata.get('attributes', [])
        for attribute in attributes:
            if attribute.get('trait_type') == 'Eyes':
                data['eyes'] = attribute.get('value', '')
                break


    assert isinstance(data, dict), f'get_ape_info{ape_id} should return a dict'
    assert all([a in data.keys() for a in
                ['owner', 'image', 'eyes']]), f"return value should include the keys 'owner','image' and 'eyes'"
    return data



# Example usage and testing
if __name__ == "__main__":
    # Test with Ape #1
    try:
        ape_info = get_ape_info(1)
        print(f"\nApe #1 Information:")
        print(f"Owner: {ape_info['owner']}")
        print(f"Image: {ape_info['image']}")
        print(f"Eyes: {ape_info['eyes']}")
    except Exception as e:
        print(f"Error: {e}")
