import os
import requests
from typing import Any, Dict

# Pinata endpoints
PINATA_PIN_URL = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
PINATA_GATEWAY_URL = "https://gateway.pinata.cloud/ipfs/"

# Read credentials from environment variables (DO NOT hard-code secrets)
# Correct usage: os.environ.get("VARIABLE_NAME", "default_value")
PINATA_API_KEY = os.environ.get("PINATA_API_KEY", "24a6c82d64ade562cafc")
PINATA_SECRET_API_KEY = os.environ.get("PINATA_SECRET_API_KEY", "5a2ff54fc754cf24fbd227e59f578921628066d4ed7ad21be2c6bfefae6057c6")


def _auth_headers_json() -> Dict[str, str]:
    """
    Build headers for Pinata authentication.
    Uses JWT if available, otherwise falls back to API key + secret.
    """
    if PINATA_API_KEY and PINATA_SECRET_API_KEY:
        return {
            "pinata_api_key": PINATA_API_KEY,
            "pinata_secret_api_key": PINATA_SECRET_API_KEY,
            "Content-Type": "application/json",
        }
    raise RuntimeError(
        "Missing Pinata credentials. Set PINATA_API_KEY and PINATA_SECRET_API_KEY as environment variables."
    )


def pin_to_ipfs(data: Dict[str, Any]) -> str:
    """
    Pin a JSON-serializable dict to IPFS via Pinata. Returns the CID string.
    """
    assert isinstance(data, dict), "pin_to_ipfs expects a dictionary"

    headers = _auth_headers_json()

    # Pinata recommends wrapping JSON content in 'pinataContent'
    payload = {"pinataContent": data}

    resp = requests.post(PINATA_PIN_URL, json=payload, headers=headers, timeout=30)

    if resp.status_code == 200:
        body = resp.json()
        cid = body.get("IpfsHash") or body.get("cid")
        if not cid:
            raise RuntimeError(f"Pinata response missing CID: {body}")
        return cid

    # Improve error messages
    try:
        details = resp.json()
    except Exception:
        details = resp.text

    if resp.status_code == 401:
        raise RuntimeError("401 Unauthorized: bad/expired JWT or API key/secret.")
    if resp.status_code == 403:
        raise RuntimeError(
            "403 Forbidden: your credential is missing pinning scope "
            "(e.g., 'pinning:pinJSONToIPFS'). Edit the key/JWT in Pinata and try again."
        )
    raise RuntimeError(f"Failed to pin to IPFS ({resp.status_code}): {details}")


def get_from_ipfs(cid: str, content_type: str = "json"):
    """
    Retrieve content from the public gateway by CID.
    If content_type='json' (default), returns a dict.
    Otherwise returns raw bytes.
    """
    assert isinstance(cid, str), "get_from_ipfs expects a CID string"

    url = f"{PINATA_GATEWAY_URL}{cid}"
    resp = requests.get(url, timeout=30)

    if resp.status_code != 200:
        try:
            details = resp.json()
        except Exception:
            details = resp.text
        raise RuntimeError(f"Failed to retrieve from IPFS ({resp.status_code}): {details}")

    if content_type.lower() == "json":
        data = resp.json()
        assert isinstance(data, dict), "get_from_ipfs('json') should return a dict"
        return data

    return resp.content
