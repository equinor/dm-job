import logging
import os
import uuid
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


class AzureHandlerProvisionError(RuntimeError):
    """ARM rejected the container-group create/update call.

    Covers quota exhaustion, invalid image references, region capacity,
    name collisions, and other non-auth ARM failures. Carries the ARM
    status code and error code so the FastAPI boundary can render a
    meaningful upstream response.
    """

    def __init__(self, message: str, status_code: int | None = None, error_code: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


def _check_required_config() -> None:
    missing = [name for name in _REQUIRED_CONFIG if not getattr(config, name, None)]
    if missing:
        raise AzureHandlerConfigError(
            "The Azure Container Instances handler cannot service this job because "
            f"job-api is missing required settings: {', '.join(missing)}. "
            "Set them as Radix secrets on the job-api component and redeploy. "
            "Other job handlers are unaffected."
        )

    # Cheap sanity check on GUID-shaped fields. AAD would reject these anyway,
    # but only after a network round-trip; a local check gives a clearer error.
    _GUID_FIELDS = (
        "AZURE_JOB_SP_CLIENT_ID",
        "AZURE_JOB_SP_TENANT_ID",
        "AZURE_JOB_SUBSCRIPTION",
    )
    bad_guids: list[str] = []
    for name in _GUID_FIELDS:
        value = getattr(config, name)
        try:
            uuid.UUID(str(value))
        except (ValueError, TypeError, AttributeError):
            bad_guids.append(f"{name}={value!r}")
    if bad_guids:
        raise AzureHandlerConfigError(
            "Azure configuration contains values that are not valid GUIDs: "
            f"{', '.join(bad_guids)}. Fix the job-api secrets and redeploy."
        )


class _JobLoggerAdapter(logging.LoggerAdapter):
    """LoggerAdapter that prepends '[job_uid=<uid>]' to every message.

    Callers can log without repeating self.job.job_uid in every f-string,
    and log aggregators can group by the prefix.
    """

    def process(self, msg, kwargs):
        return f"[job_uid={self.extra['job_uid']}] {msg}", kwargs

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
        self._log = _JobLoggerAdapter(logger, {"job_uid": self.job.job_uid})

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
        self._log.info("Starting Azure Container job...")

        # Add env-vars from deployment first
        env_vars: list[EnvironmentVariable] = [
            EnvironmentVariable(name=e, value=os.getenv(e)) for e in config.SCHEDULER_ENVS_TO_EXPORT if os.getenv(e)
        ]

        env_vars.append(EnvironmentVariable(name="DMSS_TOKEN", value=self.job.token))
        env_vars.append(EnvironmentVariable(name="DMSS_URL", value=config.GLOBAL_DMSS_URL))
        env_vars.append(EnvironmentVariable(name="DM_JOB_URL", value=config.GLOBAL_DM_JOB_URL))
        env_vars.append(EnvironmentVariable(name="JOB_DMSS_ID", value=self.job.dmss_id))

        # Parse env-vars from job entity
        logger.info("Injecting env vars from job entity")
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
        # ACI Norway East limits (per container group, at time of writing):
        #   CPU:    0.5 .. 4.0 cores
        #   Memory: 0.5 .. 16.0 GB
        # See: https://learn.microsoft.com/en-us/azure/container-instances/container-instances-region-availability
        _CPU_MIN, _CPU_MAX = 0.5, 4.0
        _MEM_MIN, _MEM_MAX = 0.5, 16.0
        if "computeResource" in runner_entity:
            compute_resource = runner_entity["computeResource"]
            requested_memory = compute_resource.get("memory", memory_in_gb)
            requested_cpu = compute_resource.get("cpu", cpu)
            memory_in_gb = max(_MEM_MIN, min(_MEM_MAX, float(requested_memory)))
            cpu = max(_CPU_MIN, min(_CPU_MAX, float(requested_cpu)))
            if memory_in_gb != requested_memory or cpu != requested_cpu:
                self._log.warning(
                    f"Requested compute resources (cpu={requested_cpu}, "
                    f"memory={requested_memory} GB) clamped to ACI limits "
                    f"(cpu={cpu}, memory={memory_in_gb} GB)."
                )

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
        except HttpResponseError as exc:
            # Non-auth ARM failures: quota, invalid image, region capacity,
            # name collisions, etc. Carry status/error codes for the API layer.
            error_code = getattr(getattr(exc, "error", None), "code", None)
            raise AzureHandlerProvisionError(
                f"Azure rejected the container-group provisioning request "
                f"(container '{self.azure_valid_container_name}'). "
                f"ARM status={exc.status_code}, code={error_code}: {exc.message}",
                status_code=exc.status_code,
                error_code=error_code,
            ) from exc

        # Poll until the container is actually running or has terminated
        max_wait_seconds = 120 * 5
        poll_interval = 5
        waited = 0
        container_state: str | None = None
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
            except (AttributeError, TypeError):
                # instance_view may not be available yet
                logger.info("Container instance view not yet available, waiting...")
            except HttpResponseError as e:
                # Handle ContainerGroupDeploymentNotReady and similar errors
                if "ContainerGroupDeploymentNotReady" in str(e) or "not ready" in str(e).lower():
                    logger.info(f"Container group not ready yet: {e.message}")
                else:
                    raise  # Re-raise if it's a different error
            sleep(poll_interval)
            waited += poll_interval
        else:
            # Loop exited via the while-condition, not via break: we timed out.
            raise TimeoutError(
                f"Azure container '{self.azure_valid_container_name}' did not "
                f"reach Running/Terminated within {max_wait_seconds}s "
                f"(last observed state: {container_state!r}). The container "
                "group has been created but is stuck - inspect ACI events "
                "(image pull, quota, networking) and remove() when done."
            )

        logger.info("*** Azure container job started successfully ***")

        return "Azure container started"

    def remove(self) -> Tuple[JobStatus, str]:
        try:
            operation = self.aci_client.container_groups.begin_delete(
                config.AZURE_JOB_RESOURCE_GROUP, self.azure_valid_container_name
            )
        except ResourceNotFoundError:
            # Idempotent: already gone counts as successfully removed.
            logger.info(
                f"Container group '{self.azure_valid_container_name}' already absent; "
                "treating remove() as completed."
            )
            return JobStatus.COMPLETED, "already removed"
        except ClientAuthenticationError as exc:
            raise AzureHandlerAuthError(
                "Azure rejected the service principal credentials during remove(). "
                f"AAD detail: {exc.message}"
            ) from exc
        except HttpResponseError as exc:
            error_code = getattr(getattr(exc, "error", None), "code", None)
            raise AzureHandlerProvisionError(
                f"Azure rejected the container-group delete request "
                f"(container '{self.azure_valid_container_name}'). "
                f"ARM status={exc.status_code}, code={error_code}: {exc.message}",
                status_code=exc.status_code,
                error_code=error_code,
            ) from exc

        # Poll deletion status
        status = operation.status()
        for _ in range(4):
            status = operation.status()
            if status in ("Succeeded", "Failed", "Canceled"):
                break
            sleep(2)

        if status == "Succeeded":
            return JobStatus.COMPLETED, status
        if status in ("Failed", "Canceled"):
            logger.warning(
                f"Delete of container '{self.azure_valid_container_name}' ended with status={status}"
            )
            return JobStatus.FAILED, status
        # Still InProgress after the polling budget - not an error, just not done.
        return JobStatus.UNKNOWN, status

    def progress(self) -> Tuple[JobStatus, None | list[str] | str, None | float]:
        """Poll progress from the job instance"""
        if self.job.status == JobStatus.FAILED:
            # If setup fails, the container is not started
            return self.job.status, self.job.log, self.job.percentage

        # Fetch container group first (cheap, single ARM round-trip). Only pull
        # logs if the container has actually reached a state that produces them.
        try:
            container_group = self.aci_client.container_groups.get(
                config.AZURE_JOB_RESOURCE_GROUP, self.azure_valid_container_name
            )
        except ResourceNotFoundError:
            raise NotFoundException(
                f"The container '{self.azure_valid_container_name}' does not exist. "
                "Either it has not been created, or it's not ready to accept requests."
            )
        except ClientAuthenticationError as exc:
            raise AzureHandlerAuthError(
                "Azure rejected the service principal credentials during progress(). "
                f"AAD detail: {exc.message}"
            ) from exc
        except HttpResponseError as e:
            if "ContainerGroupDeploymentNotReady" in str(e) or "not ready" in str(e).lower():
                logger.info(f"Container group not ready yet: {e}")
                return JobStatus.STARTING, "Container is still initializing...", self.job.percentage
            raise

        try:
            current_state = container_group.containers[0].instance_view.current_state
            status = current_state.state
            exit_code = current_state.exit_code
        except (AttributeError, TypeError):
            # instance_view may not be available yet
            return JobStatus.STARTING, "Container instance view not yet available", self.job.percentage

        # Only request logs once the container has content to produce.
        logs: None | list[str] | str = None
        if status in ("Running", "Terminated"):
            try:
                logs = self.aci_client.containers.list_logs(
                    config.AZURE_JOB_RESOURCE_GROUP,
                    self.azure_valid_container_name,
                    self.azure_valid_container_name,
                ).content
            except ResourceNotFoundError:
                logs = None
            except HttpResponseError as e:
                if "ContainerGroupDeploymentNotReady" in str(e) or "not ready" in str(e).lower():
                    logger.info(f"Container group not ready yet for log retrieval: {e}")
                    return JobStatus.STARTING, "Container is still initializing...", self.job.percentage
                raise

        if not logs:  # Fall back to Container Instance events
            try:
                logs = container_group.containers[0].instance_view.events[-1].message
            except (AttributeError, TypeError, IndexError):
                logs = self.job.log

        job_status = self.job.status

        # Flake8 does not have support for match case syntax. Using noqa to disable warnings.
        match (status, exit_code):  # noqa
            case ("Running", None):  # noqa
                job_status = JobStatus.RUNNING
            case ("Terminated", 0):  # noqa
                job_status = JobStatus.COMPLETED
            case ("Terminated", exit_code) if exit_code is not None and exit_code != 0:  # noqa
                # Includes negative exit codes (SIGKILL, OOM = -9, SIGSEGV = -11, ...)
                job_status = JobStatus.FAILED
            case ("Waiting", None):  # noqa
                job_status = JobStatus.STARTING
            case ("Succeeded", _):  # noqa - ACI provisioning succeeded, container not yet Running
                job_status = JobStatus.STARTING
            case ("Pending", _):  # noqa
                job_status = JobStatus.STARTING
            case ("Failed", _) | ("Canceled", _):  # noqa - ACI-side failures (image pull, quota, ...)
                job_status = JobStatus.FAILED
            case _:  # noqa - any state we haven't mapped
                self._log.warning(
                    f"Unmapped ACI container state: status={status!r}, exit_code={exit_code}"
                )
                job_status = JobStatus.UNKNOWN
        return job_status, logs, self.job.percentage
