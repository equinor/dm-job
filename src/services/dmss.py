import json

import requests
from dmss_api.apis import DefaultApi

from config import Config
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


def get_document(fully_qualified_path: str) -> dict:
    """
    The default DMSS document getter.
    Used by DocumentService.
    Inject a mock 'get_document' in unit.
    """
    # TODO: Update dmss endpoint to handle a singe ID string
    # TODO: Update dmss endpoint to only return the raw document, not the blueprint(?)
    data_source, path = fully_qualified_path.split("/", 1)
    dmss_api.api_client.configuration.access_token = get_access_token()
    return dmss_api.document_get_by_path(data_source, path=path)["document"]  # type: ignore


def get_document_by_uid(id_reference: str, depth: int = 999, ui_recipe="", attribute="", token: str = None) -> dict:
    """
    The uid based DMSS document getter.
    Used by DocumentService.
    Inject a mock 'get_document_by_uid' in unit unit.

    id_reference is on the format: <data_source>/<document_uuid>.<attribute>
    """

    # The generated API package was transforming data types. i.e. parsing datetime from strings...

    headers = {"Authorization": f"Bearer {token or get_access_token()}", "Access-Key": token or get_access_token()}
    params = {"depth": depth, "ui_recipe": ui_recipe, "attribute": attribute}
    req = requests.get(f"{Config.DMSS_API}/api/documents/{id_reference}", params=params, headers=headers)
    req.raise_for_status()

    return req.json()  # type: ignore


def update_document_by_uid(document_id: str, document: dict, token: str = None) -> dict:

    headers = {"Authorization": f"Bearer {token or get_access_token()}", "Access-Key": token or get_access_token()}
    form_data = {k: json.dumps(v) if isinstance(v, dict) else str(v) for k, v in document.items()}
    req = requests.put(
        f"{Config.DMSS_API}/api/documents/{document_id}",
        data=form_data,
        headers=headers,
        params={"update_uncontained": "False"},
    )
    req.raise_for_status()
    return req.json()  # type: ignore


def add_document_simple(data_source: str, document: dict, token: str = None) -> str:

    headers = {"Authorization": f"Bearer {token or get_access_token()}", "Access-Key": token or get_access_token()}
    req = requests.post(
        f"{Config.DMSS_API}/api/documents/{data_source}/add-raw",
        json=document,
        headers=headers,
    )
    req.raise_for_status()
    return req.text


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
