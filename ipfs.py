import os
import requests
from typing import Any, Dict

# Pinata API credentials
PINATA_API_KEY = '68de09698d56d5fe2518'
PINATA_SECRET_API_KEY = 'f0447bfea07bc6acad3ec708db658d44c322d71b404fe83db0e75b82e141d359'
PINATA_JWT='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiJmZDIwOTU2Zi1hNTkwLTRmNTAtYjFiNC04ZmJkNjdkNGNkZWMiLCJlbWFpbCI6IndsaXlpbmcyMUBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwicGluX3BvbGljeSI6eyJyZWdpb25zIjpbeyJkZXNpcmVkUmVwbGljYXRpb25Db3VudCI6MSwiaWQiOiJGUkExIn0seyJkZXNpcmVkUmVwbGljYXRpb25Db3VudCI6MSwiaWQiOiJOWUMxIn1dLCJ2ZXJzaW9uIjoxfSwibWZhX2VuYWJsZWQiOmZhbHNlLCJzdGF0dXMiOiJBQ1RJVkUifSwiYXV0aGVudGljYXRpb25UeXBlIjoic2NvcGVkS2V5Iiwic2NvcGVkS2V5S2V5IjoiNjhkZTA5Njk4ZDU2ZDVmZTI1MTgiLCJzY29wZWRLZXlTZWNyZXQiOiJmMDQ0N2JmZWEwN2JjNmFjYWQzZWM3MDhkYjY1OGQ0NGMzMjJkNzFiNDA0ZmU4M2RiMGU3NWI4MmUxNDFkMzU5IiwiZXhwIjoxNzkyOTM1OTk3fQ.vHzKCFmHdGtlpF_rhJlERjU7spCOdMrjMQllnSM0nPM'
PINATA_PIN_URL = 'https://api.pinata.cloud/pinning/pinJSONToIPFS'
PINATA_GATEWAY_URL = 'https://gateway.pinata.cloud/ipfs/'

import os

PINATA_API_KEY = os.environ.get("68de09698d56d5fe2518")
PINATA_SECRET_API_KEY = os.environ.get("f0447bfea07bc6acad3ec708db658d44c322d71b404fe83db0e75b82e141d359")
PINATA_JWT = os.environ.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiJmZDIwOTU2Zi1hNTkwLTRmNTAtYjFiNC04ZmJkNjdkNGNkZWMiLCJlbWFpbCI6IndsaXlpbmcyMUBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwicGluX3BvbGljeSI6eyJyZWdpb25zIjpbeyJkZXNpcmVkUmVwbGljYXRpb25Db3VudCI6MSwiaWQiOiJGUkExIn0seyJkZXNpcmVkUmVwbGljYXRpb25Db3VudCI6MSwiaWQiOiJOWUMxIn1dLCJ2ZXJzaW9uIjoxfSwibWZhX2VuYWJsZWQiOmZhbHNlLCJzdGF0dXMiOiJBQ1RJVkUifSwiYXV0aGVudGljYXRpb25UeXBlIjoic2NvcGVkS2V5Iiwic2NvcGVkS2V5S2V5IjoiNjhkZTA5Njk4ZDU2ZDVmZTI1MTgiLCJzY29wZWRLZXlTZWNyZXQiOiJmMDQ0N2JmZWEwN2JjNmFjYWQzZWM3MDhkYjY1OGQ0NGMzMjJkNzFiNDA0ZmU4M2RiMGU3NWI4MmUxNDFkMzU5IiwiZXhwIjoxNzkyOTM1OTk3fQ.vHzKCFmHdGtlpF_rhJlERjU7spCOdMrjMQllnSM0nPM")

def pin_to_ipfs(data: Dict[str, Any]) -> str:
    """Pins a JSON-serializable dict to IPFS via Pinata and returns the CID."""
    assert isinstance(data, dict), "pin_to_ipfs expects a dictionary"

    headers = _auth_headers_json()

    # Pinata recommends wrapping JSON in 'pinataContent'
    payload = {"pinataContent": data}

    r = requests.post(PINATA_PIN_URL, json=payload, headers=headers, timeout=30)

    if r.status_code == 200:
        body = r.json()
        cid = body.get("IpfsHash") or body.get("cid")
        if not cid:
            raise RuntimeError(f"Pinata response missing CID: {body}")
        return cid

    # Helpful diagnostics
    try:
        details = r.json()
    except Exception:
        details = r.text

    if r.status_code == 401:
        raise RuntimeError("Unauthorized: bad/expired JWT or API key/secret.")
    if r.status_code == 403:
        raise RuntimeError(
            "Forbidden: key/JWT missing required pinning scopes (e.g., pinJSONToIPFS)."
        )
    raise RuntimeError(f"Failed to pin to IPFS: {r.status_code}, {details}")


def get_from_ipfs(cid: str, content_type: str = "json"):
    """Fetches content from the public gateway; returns dict for JSON, bytes otherwise."""
    assert isinstance(cid, str), "get_from_ipfs expects a CID string"
    url = f"{PINATA_GATEWAY_URL}{cid}"

    r = requests.get(url, timeout=30)
    if r.status_code != 200:
        try:
            details = r.json()
        except Exception:
            details = r.text
        raise RuntimeError(f"Failed to retrieve from IPFS: {r.status_code}, {details}")

    if content_type.lower() == "json":
        data = r.json()
        assert isinstance(data, dict), "get_from_ipfs(content_type='json') should return a dict"
        return data

    # For non-JSON, return raw bytes
    return r.content
