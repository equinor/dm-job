import json

import requests

from config import Config
from dmss_api.apis import DefaultApi
from middleware.store_headers import get_access_key_header, get_auth_header

dmss_api = DefaultApi()
dmss_api.api_client.configuration.host = Config.DMSS_API


def get_access_token() -> str:
    auth_header = get_auth_header()
    if auth_header:
        head_split = auth_header.split(" ")
        if head_split[0].lower() == "bearer" and len(head_split) == 2:
            return head_split[1]  # type: ignore
        raise ValueError("Authorization header malformed. Should be; 'Bearer myAccessTokenString'")
    else:
        return ""


def get_document(reference: str, depth: int = 0, token: str | None = None) -> dict:
    # The generated API package was transforming data types. i.e. parsing datetime from strings...

    headers = {"Authorization": f"Bearer {token or get_access_token()}", "Access-Key": token or get_access_token()}
    params = {"depth": depth}
    req = requests.get(f"{Config.DMSS_API}/api/documents/{reference}", params=params, headers=headers, timeout=10)
    req.raise_for_status()

    return req.json()  # type: ignore


def update_document(reference: str, document_json: str, token: str | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token or get_access_token()}", "Access-Key": token or get_access_token()}
    req = requests.put(
        f"{Config.DMSS_API}/api/documents/{reference}",
        data={"data": document_json},
        headers=headers,
        timeout=10,
    )
    req.raise_for_status()
    return req.json()  # type: ignore


def add_document(reference: str, document: dict, token: str | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token or get_access_token()}", "Access-Key": token or get_access_token()}
    # form_data = {k: json.dumps(v) if isinstance(v, dict) else str(v) for k, v in document.items()}
    req = requests.post(
        f"{Config.DMSS_API}/api/documents/{reference}",
        data={"document": json.dumps(document)},
        headers=headers,
        timeout=10,
    )
    req.raise_for_status()
    return req.json()  # type: ignore


def get_blueprint(type_ref: str) -> dict:
    """
    Fetches a resolved blueprint from DMSS
    """
    dmss_api.api_client.default_headers["Authorization"] = "Bearer " + get_access_token()
    return dmss_api.blueprint_get(type_ref)  # type: ignore


def get_personal_access_token() -> str:
    """
    Fetches a long lived Access Token
    """
    pat_in_header = get_access_key_header()
    if pat_in_header:
        return pat_in_header  # type: ignore
    dmss_api.api_client.default_headers["Authorization"] = "Bearer " + get_access_token()
    return dmss_api.token_create()  # type: ignore
