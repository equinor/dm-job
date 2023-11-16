import uvicorn
from fastapi import APIRouter, FastAPI, Security
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2AuthorizationCodeBearer
from starlette.middleware import Middleware
from starlette.responses import RedirectResponse

from config import config
from features.jobs import jobs
from middleware.store_headers import StoreHeadersMiddleware
from restful.responses import responses
from utils.exception_handlers import validation_exception_handler
from utils.logging import logger

oauth2_scheme = OAuth2AuthorizationCodeBearer(authorizationUrl="", tokenUrl="", auto_error=False)


def auth_with_jwt(jwt_token: str = Security(oauth2_scheme)):
    # Authentication is handled by DMSS. Adding a security dependenciy is
    # necessary to generate correct JSON schema for openapi generator.
    pass


def create_app():
    all_routes = APIRouter(tags=["DMJobs"])
    authenticated_routes = APIRouter()
    authenticated_routes.include_router(jobs.router)

    app = FastAPI(
        title="Data Modelling Job API",
        responses=responses,
        version="1.3.4",  # x-release-please-version
        description="REST API used with the Data Modelling framework to schedule jobs",
        exception_handlers={RequestValidationError: validation_exception_handler},
        middleware=[Middleware(StoreHeadersMiddleware)],
        swagger_ui_init_oauth={
            "clientId": config.OAUTH_CLIENT_ID,
            "appName": "DM JOB",
            "usePkceWithAuthorizationCodeGrant": True,
            "scopes": config.OAUTH_AUTH_SCOPE,
            "useBasicAuthenticationWithAccessCodeGrant": True,
        },
    )

    if config.ENVIRONMENT == "local":
        logger.warning("CORS has been turned off. This should only occur in in development.")
        # Turn off CORS when running locally. allow_origins argument can be replaced with a list of URLs.
        app.add_middleware(
            CORSMiddleware,
            allow_origins="*",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    all_routes.include_router(authenticated_routes, dependencies=[Security(auth_with_jwt)])
    app.include_router(all_routes)

    @app.get("/", operation_id="redirect_to_docs", response_class=RedirectResponse, include_in_schema=False)
    def redirect_to_docs():
        """
        Redirects any requests to the servers root ('/') to '/docs'
        """
        return RedirectResponse(url="/docs")

    return app


def run():
    uvicorn.run(
        "app:create_app",
        host="0.0.0.0",  # nosec
        port=5000,
        reload=config.ENVIRONMENT == "local",
        factory=True,
        log_level=config.LOGGER_LEVEL.lower(),
    )


if __name__ == "__main__":
    run()
