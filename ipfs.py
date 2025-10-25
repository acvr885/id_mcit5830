import os
import requests
from typing import Any, Dict

# Pinata API credentials
PINATA_API_KEY = '68de09698d56d5fe2518'
PINATA_SECRET_API_KEY = 'f0447bfea07bc6acad3ec708db658d44c322d71b404fe83db0e75b82e141d359'
PINATA_JWT='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiJmZDIwOTU2Zi1hNTkwLTRmNTAtYjFiNC04ZmJkNjdkNGNkZWMiLCJlbWFpbCI6IndsaXlpbmcyMUBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwicGluX3BvbGljeSI6eyJyZWdpb25zIjpbeyJkZXNpcmVkUmVwbGljYXRpb25Db3VudCI6MSwiaWQiOiJGUkExIn0seyJkZXNpcmVkUmVwbGljYXRpb25Db3VudCI6MSwiaWQiOiJOWUMxIn1dLCJ2ZXJzaW9uIjoxfSwibWZhX2VuYWJsZWQiOmZhbHNlLCJzdGF0dXMiOiJBQ1RJVkUifSwiYXV0aGVudGljYXRpb25UeXBlIjoic2NvcGVkS2V5Iiwic2NvcGVkS2V5S2V5IjoiNjhkZTA5Njk4ZDU2ZDVmZTI1MTgiLCJzY29wZWRLZXlTZWNyZXQiOiJmMDQ0N2JmZWEwN2JjNmFjYWQzZWM3MDhkYjY1OGQ0NGMzMjJkNzFiNDA0ZmU4M2RiMGU3NWI4MmUxNDFkMzU5IiwiZXhwIjoxNzkyOTM1OTk3fQ.vHzKCFmHdGtlpF_rhJlERjU7spCOdMrjMQllnSM0nPM'
PINATA_PIN_URL = 'https://api.pinata.cloud/pinning/pinJSONToIPFS'
PINATA_GATEWAY_URL = 'https://gateway.pinata.cloud/ipfs/'

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
