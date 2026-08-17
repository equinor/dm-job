from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from job_handler_plugins.azure_container_instances import (
    AzureHandlerAuthError,
    AzureHandlerConfigError,
    AzureHandlerProvisionError,
)
from restful.responses import ErrorResponse


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        ErrorResponse(
            status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            type="RequestValidationError",
            message="The received values are invalid",
            debug="The received values are invalid according to the endpoints model definition",
            extra=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
        ).model_dump(),
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


async def azure_config_exception_handler(request: Request, exc: AzureHandlerConfigError):
    """The AzureContainer handler cannot service this job because job-api is
    missing (or has malformed) Azure secrets. Report as 503 - the service
    itself is running, but this backend is not configured."""
    return JSONResponse(
        ErrorResponse(
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
            type="AzureHandlerConfigError",
            message="Azure Container Instances backend is not configured on job-api.",
            debug=str(exc),
        ).model_dump(),
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        headers={"Retry-After": "300"},
    )


async def azure_auth_exception_handler(request: Request, exc: AzureHandlerAuthError):
    """AAD rejected the service-principal credentials. 502 - upstream refused
    authentication; job-api is healthy but Azure said no."""
    return JSONResponse(
        ErrorResponse(
            status=status.HTTP_502_BAD_GATEWAY,
            type="AzureHandlerAuthError",
            message="Azure AD rejected the job-api service-principal credentials.",
            debug=str(exc),
        ).model_dump(),
        status_code=status.HTTP_502_BAD_GATEWAY,
    )


async def azure_provision_exception_handler(request: Request, exc: AzureHandlerProvisionError):
    """ARM rejected the container-group create/delete request for a non-auth
    reason (quota, invalid image, region capacity, name collision, ...)."""
    return JSONResponse(
        ErrorResponse(
            status=status.HTTP_502_BAD_GATEWAY,
            type="AzureHandlerProvisionError",
            message="Azure Resource Manager rejected the container-group operation.",
            debug=str(exc),
            extra={"arm_status_code": exc.status_code, "arm_error_code": exc.error_code},
        ).model_dump(),
        status_code=status.HTTP_502_BAD_GATEWAY,
    )
