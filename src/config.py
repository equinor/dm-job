import os


class Config:
    LOGGER_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")
    API_DEBUG = os.getenv("API_DEBUG", 0)
    ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
    DMSS_API = os.getenv("DMSS_API", "http://dmss:5000")

    # Azure stuff
    # Where to run jobs in Azure
    AZURE_JOB_SUBSCRIPTION = os.getenv("AZURE_JOB_SUBSCRIPTION")
    AZURE_JOB_RESOURCE_GROUP = os.getenv("AZURE_JOB_RESOURCE_GROUP")
    # Which ServicePrincipal to authenticate with
    AZURE_JOB_SP_SECRET = os.getenv("AZURE_SP_SECRET")
    AZURE_JOB_SP_CLIENT_ID = os.getenv("AZURE_JOB_CLIENT_ID")
    AZURE_JOB_SP_TENANT_ID = os.getenv("AZURE_JOB_TENANT_ID")

    # Allows for some per-deployment environment variables to be passed to jobs
    SCHEDULER_ENVS_TO_EXPORT = (
        os.getenv("SCHEDULER_ENVS_TO_EXPORT", "").split(",") if os.getenv("SCHEDULER_ENVS_TO_EXPORT") else []
    )

    # Redis stuff
    SCHEDULER_REDIS_PASSWORD = os.getenv("SCHEDULER_REDIS_PASSWORD")
    SCHEDULER_REDIS_HOST = os.getenv("SCHEDULER_REDIS_HOST", "job-store")
    SCHEDULER_REDIS_PORT = int(os.getenv("SCHEDULER_REDIS_PORT", 6379))
    SCHEDULER_REDIS_SSL = os.getenv("SCHEDULER_REDIS_SSL", "False").lower() == "true"

    # Swagger auth
    OAUTH_CLIENT_ID: str | None = os.getenv("OAUTH_CLIENT_ID")
    OAUTH_AUTH_SCOPE: str | None = os.getenv("OAUTH_AUTH_SCOPE")

    RECURRING_JOB = "dmss://WorkflowDS/Blueprints/RecurringJob"


config = Config()
