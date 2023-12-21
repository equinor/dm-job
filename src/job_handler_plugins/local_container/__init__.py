import os
from typing import Tuple

import docker
from docker.errors import APIError, DockerException, ImageNotFound

from config import config
from restful.exceptions import NotFoundException, NotImplementedException
from services.job_handler_interface import Job, JobHandlerInterface, JobStatus
from utils.logging import logger

_SUPPORTED_TYPE = "dmss://WorkflowDS/Blueprints/LocalContainer"


class JobHandler(JobHandlerInterface):
    """
    A job handler to run local docker container. This is similar to the local_containers job handler in DMT, but uses
    a different blueprint
    """

    # todo consider implementing a pydantic class to check that job_entity is in correct format
    def __init__(self, job: Job, data_source: str):
        super().__init__(job, data_source)
        self.headers = {"Access-Key": job.token}
        self.local_container_name = f"{job.runner['name']}_{str(job.job_uid).split('-')[0]}"
        try:
            self.client = docker.from_env()
        except DockerException:
            raise NotImplementedException(
                "Support for running local containers has not been configured for this environment",
                debug=(
                    "Failed to get a docker client. Docker must be installed on this host, or "
                    + "the /var/run/docker.sock must be made available (volume mount)."
                    + "Make sure you are aware of the serious security risk this entails."
                ),
            )

    def start(self) -> str:
        runner_entity: dict = self.job.runner
        full_image_name: str = (
            f"{runner_entity['image']['registryName']}/{runner_entity['image']['imageName']}"
            + f":{runner_entity['image']['version']}"
        )
        envs = [f"{e}={os.getenv(e)}" for e in config.SCHEDULER_ENVS_TO_EXPORT if os.getenv(e)]

        custom_command = self.job.runner.get("customCommands")
        envs = envs + runner_entity.get("environmentVariables", [])
        envs.append(f"DMSS_TOKEN={self.job.token}")
        envs.append(f"DMSS_ID={self.job.dmss_id}")
        envs.append(f"DMSS_URL={config.DMSS_API}")
        envs.append(f"JOB_API_URL={config.JOB_API_URL}")

        try:
            self.client.containers.run(
                image=full_image_name,
                command=custom_command,
                name=self.local_container_name,
                environment=envs,
                network=self.job.runner["network"],
                detach=True,
            )
        except (ImageNotFound, APIError) as ex:
            raise NotFoundException(
                f"No image named '{full_image_name}' could be found. Sure it is published and that you have access?"
            ) from ex
        message = "*** Local container job started successfully ***"
        return message

    def remove(self) -> Tuple[JobStatus, str]:
        try:
            container = self.client.containers.get(self.local_container_name)
            if container.status != "exited":
                container.kill()
            container.remove()
        except docker.errors.NotFound:
            logger.info(f"Docker container {self.local_container_name} was not found")
        return JobStatus.REMOVED, f"Removed docker container {self.local_container_name}"

    def progress(self) -> Tuple[JobStatus, None | list[str] | str, None | float]:
        """Poll progress from the job instance"""
        try:
            container = self.client.containers.get(self.local_container_name)
            if container.status == "running":
                return JobStatus.RUNNING, "Job is running", 0
            elif container.attrs["State"]["ExitCode"] == 0:
                return JobStatus.COMPLETED, "Local container completed successfully", 1
            else:
                return (
                    JobStatus.FAILED,
                    "Job failed for an unknown reason. Consider implementing job progress update for more details.",
                    0,
                )
        except docker.errors.NotFound as error:
            return JobStatus.UNKNOWN, f"Failed to poll progress of local container: {error}", None

    def result(self) -> Tuple[str, bytes]:
        return "test 123", b"lkjgfdakljhfdgsllkjhldafgoiu8y03q987hgbloizdjhfpg980"
