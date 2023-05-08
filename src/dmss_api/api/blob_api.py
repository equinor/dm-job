"""
    Data Modelling Storage Service

    API for basic data modelling interaction  # noqa: E501

    The version of the OpenAPI document: 0.1.0
    Generated by: https://openapi-generator.tech
"""


import re  # noqa: F401
import sys  # noqa: F401

from dm_cli.dmss_api.api_client import ApiClient, Endpoint as _Endpoint
from dm_cli.dmss_api.model_utils import (  # noqa: F401
    check_allowed_values,
    check_validations,
    date,
    datetime,
    file_type,
    none_type,
    validate_and_convert_types
)
from dm_cli.dmss_api.model.error_response import ErrorResponse


class BlobApi(object):
    """NOTE: This class is auto generated by OpenAPI Generator
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    def __init__(self, api_client=None):
        if api_client is None:
            api_client = ApiClient()
        self.api_client = api_client

        def __blob_get_by_id(
            self,
            data_source_id,
            blob_id,
            **kwargs
        ):
            """Get By Id  # noqa: E501

            Get blob from id. A blob (binary large object) can be anything from video to text file.  # noqa: E501
            This method makes a synchronous HTTP request by default. To make an
            asynchronous HTTP request, please pass async_req=True

            >>> thread = api.blob_get_by_id(data_source_id, blob_id, async_req=True)
            >>> result = thread.get()

            Args:
                data_source_id (str):
                blob_id (str):

            Keyword Args:
                _return_http_data_only (bool): response data without head status
                    code and headers. Default is True.
                _preload_content (bool): if False, the urllib3.HTTPResponse object
                    will be returned without reading/decoding response data.
                    Default is True.
                _request_timeout (int/float/tuple): timeout setting for this request. If
                    one number provided, it will be total request timeout. It can also
                    be a pair (tuple) of (connection, read) timeouts.
                    Default is None.
                _check_input_type (bool): specifies if type checking
                    should be done one the data sent to the server.
                    Default is True.
                _check_return_type (bool): specifies if type checking
                    should be done one the data received from the server.
                    Default is True.
                _host_index (int/None): specifies the index of the server
                    that we want to use.
                    Default is read from the configuration.
                async_req (bool): execute request asynchronously

            Returns:
                file_type
                    If the method is called asynchronously, returns the request
                    thread.
            """
            kwargs['async_req'] = kwargs.get(
                'async_req', False
            )
            kwargs['_return_http_data_only'] = kwargs.get(
                '_return_http_data_only', True
            )
            kwargs['_preload_content'] = kwargs.get(
                '_preload_content', True
            )
            kwargs['_request_timeout'] = kwargs.get(
                '_request_timeout', None
            )
            kwargs['_check_input_type'] = kwargs.get(
                '_check_input_type', True
            )
            kwargs['_check_return_type'] = kwargs.get(
                '_check_return_type', True
            )
            kwargs['_host_index'] = kwargs.get('_host_index')
            kwargs['data_source_id'] = \
                data_source_id
            kwargs['blob_id'] = \
                blob_id
            return self.call_with_http_info(**kwargs)

        self.blob_get_by_id = _Endpoint(
            settings={
                'response_type': (file_type,),
                'auth': [
                    'APIKeyHeader',
                    'OAuth2AuthorizationCodeBearer'
                ],
                'endpoint_path': '/api/blobs/{data_source_id}/{blob_id}',
                'operation_id': 'blob_get_by_id',
                'http_method': 'GET',
                'servers': None,
            },
            params_map={
                'all': [
                    'data_source_id',
                    'blob_id',
                ],
                'required': [
                    'data_source_id',
                    'blob_id',
                ],
                'nullable': [
                ],
                'enum': [
                ],
                'validation': [
                ]
            },
            root_map={
                'validations': {
                },
                'allowed_values': {
                },
                'openapi_types': {
                    'data_source_id':
                        (str,),
                    'blob_id':
                        (str,),
                },
                'attribute_map': {
                    'data_source_id': 'data_source_id',
                    'blob_id': 'blob_id',
                },
                'location_map': {
                    'data_source_id': 'path',
                    'blob_id': 'path',
                },
                'collection_format_map': {
                }
            },
            headers_map={
                'accept': [
                    'application/octet-stream',
                    'application/json',
                    'text/plain'
                ],
                'content_type': [],
            },
            api_client=api_client,
            callable=__blob_get_by_id
        )

        def __blob_upload(
            self,
            data_source_id,
            blob_id,
            file,
            **kwargs
        ):
            """Upload  # noqa: E501

            Upload a new blob. A blob (binary large object) can be anything from video to text file.  # noqa: E501
            This method makes a synchronous HTTP request by default. To make an
            asynchronous HTTP request, please pass async_req=True

            >>> thread = api.blob_upload(data_source_id, blob_id, file, async_req=True)
            >>> result = thread.get()

            Args:
                data_source_id (str):
                blob_id (str):
                file (file_type):

            Keyword Args:
                _return_http_data_only (bool): response data without head status
                    code and headers. Default is True.
                _preload_content (bool): if False, the urllib3.HTTPResponse object
                    will be returned without reading/decoding response data.
                    Default is True.
                _request_timeout (int/float/tuple): timeout setting for this request. If
                    one number provided, it will be total request timeout. It can also
                    be a pair (tuple) of (connection, read) timeouts.
                    Default is None.
                _check_input_type (bool): specifies if type checking
                    should be done one the data sent to the server.
                    Default is True.
                _check_return_type (bool): specifies if type checking
                    should be done one the data received from the server.
                    Default is True.
                _host_index (int/None): specifies the index of the server
                    that we want to use.
                    Default is read from the configuration.
                async_req (bool): execute request asynchronously

            Returns:
                str
                    If the method is called asynchronously, returns the request
                    thread.
            """
            kwargs['async_req'] = kwargs.get(
                'async_req', False
            )
            kwargs['_return_http_data_only'] = kwargs.get(
                '_return_http_data_only', True
            )
            kwargs['_preload_content'] = kwargs.get(
                '_preload_content', True
            )
            kwargs['_request_timeout'] = kwargs.get(
                '_request_timeout', None
            )
            kwargs['_check_input_type'] = kwargs.get(
                '_check_input_type', True
            )
            kwargs['_check_return_type'] = kwargs.get(
                '_check_return_type', True
            )
            kwargs['_host_index'] = kwargs.get('_host_index')
            kwargs['data_source_id'] = \
                data_source_id
            kwargs['blob_id'] = \
                blob_id
            kwargs['file'] = \
                file
            return self.call_with_http_info(**kwargs)

        self.blob_upload = _Endpoint(
            settings={
                'response_type': (str,),
                'auth': [
                    'APIKeyHeader',
                    'OAuth2AuthorizationCodeBearer'
                ],
                'endpoint_path': '/api/blobs/{data_source_id}/{blob_id}',
                'operation_id': 'blob_upload',
                'http_method': 'PUT',
                'servers': None,
            },
            params_map={
                'all': [
                    'data_source_id',
                    'blob_id',
                    'file',
                ],
                'required': [
                    'data_source_id',
                    'blob_id',
                    'file',
                ],
                'nullable': [
                ],
                'enum': [
                ],
                'validation': [
                ]
            },
            root_map={
                'validations': {
                },
                'allowed_values': {
                },
                'openapi_types': {
                    'data_source_id':
                        (str,),
                    'blob_id':
                        (str,),
                    'file':
                        (file_type,),
                },
                'attribute_map': {
                    'data_source_id': 'data_source_id',
                    'blob_id': 'blob_id',
                    'file': 'file',
                },
                'location_map': {
                    'data_source_id': 'path',
                    'blob_id': 'path',
                    'file': 'form',
                },
                'collection_format_map': {
                }
            },
            headers_map={
                'accept': [
                    'application/json',
                    'text/plain'
                ],
                'content_type': [
                    'multipart/form-data'
                ]
            },
            api_client=api_client,
            callable=__blob_upload
        )