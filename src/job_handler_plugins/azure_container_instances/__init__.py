import logging
import os
from collections import namedtuple
from time import sleep
from typing import Tuple

from azure.core.exceptions import ClientAuthenticationError, HttpResponseError, ResourceNotFoundError
from azure.identity import ClientSecretCredential
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.containerinstance.models import (
    Container,
    ContainerGroup,
    ContainerGroupRestartPolicy,
    EnvironmentVariable,
    ImageRegistryCredential,
    OperatingSystemTypes,
    ResourceRequests,
    ResourceRequirements,
)

from config import config
from restful.exceptions import NotFoundException
from services.job_handler_interface import JobHandlerInterface, JobStatus
from utils.logging import logger

AccessToken = namedtuple("AccessToken", ["token", "expires_on"])
logging.getLogger("azure").setLevel(logging.WARNING)

_SUPPORTED_TYPE = "dmss://WorkflowDS/Blueprints/AzureContainer"

# Settings that must be present on job-api for this handler to run.
# Only enforced when an AzureContainer job is actually submitted, so deployments
# that use other backends (Radix, LocalContainer, ...) do not need Azure secrets.
_REQUIRED_CONFIG = (
    "AZURE_JOB_SP_CLIENT_ID",
    "AZURE_JOB_SP_SECRET",
    "AZURE_JOB_SP_TENANT_ID",
    "AZURE_JOB_SUBSCRIPTION",
    "AZURE_JOB_RESOURCE_GROUP",
    "IMAGE_REGISTRY_USERNAME",
    "IMAGE_REGISTRY_PASSWORD",
)


class AzureHandlerConfigError(RuntimeError):
    """Missing or invalid Azure configuration.

    Only raised when an AzureContainer job is actually acted on. Other job
    handlers are unaffected, so a deployment that never uses this backend can
    run without any Azure secrets being set.
    """


class AzureHandlerAuthError(RuntimeError):
    """Azure credentials are present but rejected by AAD (expired secret, etc.)."""


def _check_required_config() -> None:
    missing = [name for name in _REQUIRED_CONFIG if not getattr(config, name, None)]
    if missing:
        raise AzureHandlerConfigError(
            "The Azure Container Instances handler cannot service this job because "
            f"job-api is missing required settings: {', '.join(missing)}. "
            "Set them as Radix secrets on the job-api component and redeploy. "
            "Other job handlers are unaffected."
        )

# Interface for Azure


class JobHandler(JobHandlerInterface):
    """
    Job handler plugin for Azure Container Instances.
    Support both executable jobs and job services
    """

    def __init__(self, job, data_source: str):
        super().__init__(job, data_source)
        # No config access or SDK construction here. This constructor runs
        # whenever the dispatcher touches a job whose runner.type happens to be
        # 'AzureContainer' - including status polls for completed jobs - and
        # would otherwise crash deployments that only use other backends.
        self.azure_valid_container_name = (
            self.job.runner["name"].lower().replace(".", "-").replace("_", "-")
        )
        self._aci_client: ContainerInstanceManagementClient | None = None

    @property
    def aci_client(self) -> ContainerInstanceManagementClient:
        """ContainerInstanceManagementClient built on first use.

        Config validation and credential construction are deferred until an
        Azure operation is actually needed, so a job-api without Azure secrets
        can still service Radix/LocalContainer jobs.
        """
        if self._aci_client is None:
            _check_required_config()
            try:
                credentials = ClientSecretCredential(
                    client_id=config.AZURE_JOB_SP_CLIENT_ID,
                    client_secret=config.AZURE_JOB_SP_SECRET,
                    tenant_id=config.AZURE_JOB_SP_TENANT_ID,
                )
            except ValueError as exc:  # e.g. tenant_id not a valid GUID
                raise AzureHandlerConfigError(
                    f"Invalid Azure credential configuration: {exc}"
                ) from exc
            self._aci_client = ContainerInstanceManagementClient(
                credentials, subscription_id=config.AZURE_JOB_SUBSCRIPTION
            )
        return self._aci_client

    def teardown_service(self, service_id: str) -> str:
        raise NotImplementedError

    def setup_service(self, service_id: str) -> str:
        raise NotImplementedError

    def start(self) -> str:
        logger.info(f"JobName: '{self.job.job_uid}'. Starting Azure Container job...")

        # Add env-vars from deployment first
        env_vars: list[EnvironmentVariable] = [
            EnvironmentVariable(name=e, value=os.getenv(e)) for e in config.SCHEDULER_ENVS_TO_EXPORT if os.getenv(e)
        ]

        env_vars.append(EnvironmentVariable(name="DMSS_TOKEN", value=self.job.token))
        env_vars.append(EnvironmentVariable(name="DMSS_URL", value=config.GLOBAL_DMSS_URL))
        env_vars.append(EnvironmentVariable(name="DM_JOB_URL", value=config.GLOBAL_DM_JOB_URL))
        env_vars.append(EnvironmentVariable(name="JOB_DMSS_ID", value=self.job.dmss_id))

        # Parse env-vars from job entity
        print("*****  Injecting env vars from job entity *****")
        for env_string in self.job.runner.get("environmentVariables", []):
            if "=" in env_string:
                key, value = env_string.split("=", 1)
            else:
                key = env_string
                if key not in os.environ:
                    logger.warning(
                        f"Environment variable '{key}' specified in job runner but not found in environment. Skipping."
                    )
                    continue
                value = os.getenv(key)
            env_vars.append(EnvironmentVariable(name=key, value=value))

        reference_target: str = self.job.referenceTarget
        runner_entity: dict = self.job.runner
        if not runner_entity["image"]["registryName"]:
            raise ValueError(
                "Runner entity is missing 'image.registryName'. "
                f"(runner: {runner_entity.get('name', '<unknown>')})"
            )
        full_image_name: str = (
            f"{runner_entity['image']['registryName']}/{runner_entity['image']['imageName']}"
            + f":{runner_entity['image']['version']}"
        )
        logger.info(
            f"Creating Azure container '{self.azure_valid_container_name}':\n\t"
            + f"Image: '{full_image_name}'\n\t"
            + "RegistryUsername: 'None'"
        )
        memory_in_gb = 2.0
        cpu = 2.0
        if "computeResource" in runner_entity:
            compute_resource = runner_entity["computeResource"]
            if "memory" in compute_resource:
                memory_in_gb = compute_resource["memory"]
            if "cpu" in compute_resource:
                cpu = compute_resource["cpu"]
            if memory_in_gb < 0.5 or cpu < 0.5:
                logger.warning(
                    f"Specified compute resources for job '{self.job.job_uid}' are below the minimum of 0.5 CPU and 0.5 GB memory. "
                    + "Using default values of 2 CPU and 2 GB memory."
                )
                memory_in_gb = 2.0
                cpu = 2.0
            if memory_in_gb > 16.0 or cpu > 4.0:
                logger.warning(
                    f"Specified compute resources for job '{self.job.job_uid}' are above the maximum of 16 CPU and 4 GB memory. "
                    + "Using default values of 2 CPU and 2 GB memory."
                )
                memory_in_gb = 2.0
                cpu = 2.0

        command_list = ["/app/main/start.sh"]
        if reference_target:
            command_list.append(f"--reference-target={reference_target}")
        compute_resources = ResourceRequests(memory_in_gb=memory_in_gb, cpu=cpu)
        container = Container(
            name=self.azure_valid_container_name,
            image=full_image_name,
            resources=ResourceRequirements(requests=compute_resources),
            command=command_list,
            environment_variables=env_vars,
        )
        image_registry_credential = ImageRegistryCredential(
            server=runner_entity["image"]["registryName"],
            username=config.IMAGE_REGISTRY_USERNAME,
            password=config.IMAGE_REGISTRY_PASSWORD,
        )

        # Configure the container group
        group = ContainerGroup(
            location="norwayeast",
            containers=[container],
            os_type=OperatingSystemTypes.linux,
            restart_policy=ContainerGroupRestartPolicy.never,
            image_registry_credentials=[image_registry_credential],
        )

        # Create the container group
        try:
            result = self.aci_client.container_groups.begin_create_or_update(
                config.AZURE_JOB_RESOURCE_GROUP, self.azure_valid_container_name, group
            )

            # Wait for the container group to be created and running
            # The begin_create_or_update() returns an LROPoller, we need to wait for it to complete
            logger.info("Waiting for Azure container group to be provisioned...")
            print("Waiting for Azure container group to be provisioned...")
            result.result()  # This blocks until the operation completes
        except ClientAuthenticationError as exc:
            # AADSTS7000215 (invalid secret), 7000222 (expired secret),
            # 700016 (unknown app), etc. Surface as a distinct exception so the
            # FastAPI boundary can return 502 instead of a bare 500.
            raise AzureHandlerAuthError(
                "Azure rejected the service principal credentials while starting "
                "the container group. The secret is most likely invalid or expired "
                f"(check the Radix job-api secrets). AAD detail: {exc.message}"
            ) from exc

        # Poll until the container is actually running or has terminated
        max_wait_seconds = 120 * 5
        poll_interval = 5
        waited = 0
        while waited < max_wait_seconds:
            try:
                container_group = self.aci_client.container_groups.get(
                    config.AZURE_JOB_RESOURCE_GROUP, self.azure_valid_container_name
                )
                container_state = container_group.containers[0].instance_view.current_state.state
                if container_state in ("Running", "Terminated"):
                    logger.info(f"Container is now in state: {container_state}")
                    break
                logger.info(f"Container state: {container_state}, waiting...")
                print(f"Container state: {container_state}, waiting...")
            except (AttributeError, TypeError):
                # instance_view may not be available yet
                logger.info("Container instance view not yet available, waiting...")
                print("Container instance view not yet available, waiting...")
            except HttpResponseError as e:
                # Handle ContainerGroupDeploymentNotReady and similar errors
                if "ContainerGroupDeploymentNotReady" in str(e) or "not ready" in str(e).lower():
                    logger.info(f"Container group not ready yet: {e.message}")
                    print(f"Container group not ready yet, waiting. : {e.message}")
                else:
                    raise  # Re-raise if it's a different error
            sleep(poll_interval)
            waited += poll_interval

        logger.info("*** Azure container job started successfully ***")
        print("*** Azure container job started successfully ***")

        return "Azure container started"

    def remove(self) -> Tuple[JobStatus, str]:
        logger.setLevel(logging.WARNING)
        operation = self.aci_client.container_groups.begin_delete(
            config.AZURE_JOB_RESOURCE_GROUP, self.azure_valid_container_name
        )
        logger.setLevel(config.LOGGER_LEVEL)
        status = operation.status()
        for i in range(4):
            status = operation.status()
            if status == "Succeeded":
                break
            sleep(2)
        job_status = JobStatus.UNKNOWN
        if status == "Succeeded":
            job_status = JobStatus.COMPLETED
        return job_status, status

    def progress(self) -> Tuple[JobStatus, None | list[str] | str, None | float]:
        """Poll progress from the job instance"""
        if self.job.status == JobStatus.FAILED:
            # If setup fails, the container is not started
            return self.job.status, self.job.log, self.job.percentage
        try:
            logger.setLevel(logging.WARNING)
            logs = self.aci_client.containers.list_logs(
                config.AZURE_JOB_RESOURCE_GROUP, self.azure_valid_container_name, self.azure_valid_container_name
            ).content
            logger.setLevel(config.LOGGER_LEVEL)
        except ResourceNotFoundError:
            raise NotFoundException(
                f"The container '{self.azure_valid_container_name}' does not exist. "
                + "Either it has not been created, or it's not ready to accept requests."
            )
        except HttpResponseError as e:
            # Handle ContainerGroupDeploymentNotReady - container is still initializing
            if "ContainerGroupDeploymentNotReady" in str(e) or "not ready" in str(e).lower():
                logger.info(f"Container group not ready yet for log retrieval: {e}")
                return JobStatus.STARTING, "Container is still initializing...", self.job.percentage
            raise

        try:
            container_group = self.aci_client.container_groups.get(
                config.AZURE_JOB_RESOURCE_GROUP, self.azure_valid_container_name
            )
            status = container_group.containers[0].instance_view.current_state.state
            exit_code = container_group.containers[0].instance_view.current_state.exit_code
        except HttpResponseError as e:
            # Handle ContainerGroupDeploymentNotReady when getting container group status
            if "ContainerGroupDeploymentNotReady" in str(e) or "not ready" in str(e).lower():
                logger.info(f"Container group not ready yet: {e}")
                return JobStatus.STARTING, "Container is still initializing...", self.job.percentage
            raise
        except (AttributeError, TypeError):
            # instance_view may not be available yet
            return JobStatus.STARTING, "Container instance view not yet available", self.job.percentage
        if not logs:  # If no container logs, get the Container Instance events instead
            try:
                logs = container_group.containers[0].instance_view.events[-1].message
            except TypeError:
                logs = self.job.log
                pass

        job_status = self.job.status

        # Flake8 does not have support for match case syntax. Using noqa to disable warnings.
        match (status, exit_code):  # noqa
            case ("Running", None):  # noqa
                job_status = JobStatus.RUNNING
            case ("Terminated", 0):  # noqa
                job_status = JobStatus.COMPLETED
            case ("Terminated", exit_code) if exit_code >= 1:  # noqa
                job_status = JobStatus.FAILED
            case ("Waiting", None):  # noqa
                job_status = JobStatus.STARTING
        return job_status, logs, self.job.percentage
