import requests
import json

# Pinata API credentials
PINATA_API_KEY = '5651b19fb2bd80d1c4f8'

PINATA_PIN_URL = 'https://api.pinata.cloud/pinning/pinJSONToIPFS'
PINATA_GATEWAY_URL = 'https://gateway.pinata.cloud/ipfs/'

def pin_to_ipfs(data):
	assert isinstance(data,dict), f"Error pin_to_ipfs expects a dictionary"
	
	# Set up headers with API authentication
	headers = {
		'pinata_api_key': PINATA_API_KEY,
		'pinata_secret_api_key': PINATA_SECRET_API_KEY,
		'Content-Type': 'application/json'
	}
	
	# Send POST request to pin JSON data to IPFS
	response = requests.post(PINATA_PIN_URL, json=data, headers=headers)
	
	# Check if the request was successful
	if response.status_code == 200:
		cid = response.json()['IpfsHash']
		return cid
	else:
		raise Exception(f"Failed to pin to IPFS: {response.status_code}, {response.text}")

def get_from_ipfs(cid, content_type="json"):
	assert isinstance(cid,str), f"get_from_ipfs accepts a cid in the form of a string"
	
	# Build the IPFS gateway URL
	url = f'{PINATA_GATEWAY_URL}{cid}'
	
	# Send GET request to retrieve data from IPFS
	response = requests.get(url)
	
	# Check if the request was successful
	if response.status_code == 200:
		data = response.json()
		assert isinstance(data,dict), f"get_from_ipfs should return a dict"
		return data
	else:
		raise Exception(f"Failed to retrieve from IPFS: {response.status_code}, {response.text}")
