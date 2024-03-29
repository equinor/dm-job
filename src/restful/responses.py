import functools
import logging
import sys
import traceback
from typing import Callable, Type, TypeVar
from uuid import uuid4

from pydantic import BaseModel
from pydantic.error_wrappers import ValidationError
from requests import HTTPError
from starlette import status
from starlette.responses import JSONResponse, PlainTextResponse, Response

from dmss_api.exceptions import ServiceException
from restful.exceptions import (
    ApplicationException,
    BadRequestException,
    MissingPrivilegeException,
    NotFoundException,
    NotImplementedException,
    ValidationException,
)
from utils.logging import logger


# Pydantic models can not inherit from "Exception", but we use it for openapi spec
class ErrorResponse(BaseModel):
    status: int = 500
    type: str = "ApplicationException"
    message: str = "The requested operation failed"
    debug: str = "An unknown and unhandled exception occurred in the API"
    data: dict | None = None


responses = {
    400: {"model": ErrorResponse, "content": {"application/json": {"example": BadRequestException().dict()}}},
    401: {
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": ErrorResponse(
                    status=401, type="UnauthorizedException", message="Token validation failed"
                ).dict()
            }
        },
    },
    403: {"model": ErrorResponse, "content": {"application/json": {"example": MissingPrivilegeException().dict()}}},
    404: {"model": ErrorResponse, "content": {"application/json": {"example": NotFoundException().dict()}}},
    422: {"model": ErrorResponse, "content": {"application/json": {"example": ValidationException().dict()}}},
    500: {"model": ErrorResponse, "content": {"application/json": {"example": ApplicationException().dict()}}},
}

TResponse = TypeVar("TResponse", bound=Response)

"""
Function made to be used as a decorator for a route.
It will execute the function, and return a successfull response of the passed response class.
If the execution fails, it will return a JSONResponse with a standardized error model.
"""


def create_response(response_class: Type[TResponse]) -> Callable[..., Callable[..., TResponse | JSONResponse]]:
    def func_wrapper(func) -> Callable[..., TResponse | JSONResponse]:
        @functools.wraps(func)
        def wrapper_decorator(*args, **kwargs) -> TResponse | JSONResponse:
            try:
                result = func(*args, **kwargs)
                return response_class(result, status_code=status.HTTP_200_OK)
            except HTTPError as http_error:
                if logger.level <= logging.DEBUG:
                    traceback.print_exc()
                error_response = ErrorResponse()
                # If we check that http_error.response exists before accessing props, it will always fail...
                if http_error.response.text:  # type: ignore
                    error_response = ErrorResponse(
                        status=http_error.response.status_code,  # type: ignore
                        message=http_error.response.text,  # type: ignore
                        debug=f"The HTTP call to '{http_error.response.url}' failed",  # type: ignore
                    )
                logger.error(error_response)
                return JSONResponse(error_response.dict(), status_code=error_response.status)
            except ServiceException as dmss_exception:
                error_id = uuid4()
                logger.error(dmss_exception, extra={"UUID": str(error_id), "Traceback": get_traceback()})
                return PlainTextResponse(str(dmss_exception), status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
            except ValidationException as e:
                if logger.level <= logging.DEBUG:
                    traceback.print_exc()
                logger.debug(e)
                return JSONResponse(e.dict(), status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
            except ValidationError as e:
                validation_exception = ValidationException(message=str(e))
                if logger.level <= logging.DEBUG:
                    traceback.print_exc()
                return JSONResponse(validation_exception.dict(), status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
            except NotFoundException as e:
                logger.debug(e)
                return JSONResponse(e.dict(), status_code=status.HTTP_404_NOT_FOUND)
            except BadRequestException as e:
                if logger.level <= logging.DEBUG:
                    traceback.print_exc()
                logger.debug(e.dict(), extra={"Traceback": get_traceback()})
                return JSONResponse(e.dict(), status_code=status.HTTP_400_BAD_REQUEST)
            except MissingPrivilegeException as e:
                logger.warning(e)
                return JSONResponse(e.dict(), status_code=status.HTTP_403_FORBIDDEN)
            except NotImplementedException as e:
                logger.warning(e)
                return JSONResponse(e.dict(), status_code=status.HTTP_501_NOT_IMPLEMENTED)
            except Exception as e:
                error_id = uuid4()
                traceback.print_exc()
                logger.error(
                    f"Unexpected unhandled exception: {e}", extra={"UUID": str(error_id), "Traceback": get_traceback()}
                )
                return JSONResponse(ErrorResponse().dict(), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return wrapper_decorator

    return func_wrapper


def get_traceback() -> str:
    """Get traceback as a log-friendly format."""
    exc_info = sys.exc_info()
    stack = traceback.extract_stack()
    tb = traceback.extract_tb(exc_info[2])
    full_tb = stack[:-1] + tb
    exc_line = traceback.format_exception_only(*exc_info[:2])
    return "Traceback (most recent call last):\n" + "".join(traceback.format_list(full_tb)) + "".join(exc_line)
