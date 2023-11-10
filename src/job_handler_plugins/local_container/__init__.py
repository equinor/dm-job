import os
from typing import Tuple

import docker
from docker.errors import DockerException

from config import config
from services.job_handler_interface import Job, JobHandlerInterface, JobStatus
from utils.logging import logger

_SUPPORTED_TYPE = "dmss://WorkflowDS/Blueprints/Container"


class JobHandler(JobHandlerInterface):
    """
    A job handler to run local docker container. This is similar to the local_containers job handler in DMT, but uses
    a different blueprint
    """

    # todo consider implementing a pydantic class to check that job_entity is in correct format
    def __init__(self, job: Job, data_source: str):
        super().__init__(job, data_source)
        self.headers = {"Access-Key": job.token}

        self.local_container_name = f"{job.entity['runner']['name']}_{str(job.job_uid).split('-')[0]}"
        try:
            self.client = docker.from_env()
        except DockerException:
            raise DockerException(
                (
                    "Failed to get a docker client. Docker must be installed on this host, or "
                    + "the /var/run/docker.sock must be made available (volume mount)."
                    + "Make sure you are aware of the serious security risk this entails."
                )
            )

    def start(self) -> str:
        runner_entity: dict = self.job.entity["runner"]
        full_image_name: str = (
            f"{runner_entity['image']['registryName']}/{runner_entity['image']['imageName']}"
            + f":{runner_entity['image']['version']}"
        )
        logger.info(f"Job path: '{self.job.dmss_id} ({self.job.job_uid})'." + " Starting Local Container job...")
        logger.info("Creating container\n\t" + f"Image: '{full_image_name}'\n\t")
        envs = [f"{e}={os.getenv(e)}" for e in config.SCHEDULER_ENVS_TO_EXPORT if os.getenv(e)]

        custom_command = self.job.entity["runner"].get("customCommands")
        envs = envs + runner_entity["environmentVariables"]
        envs.append(f"DMSS_TOKEN={self.job.token}")
        envs.append(f"DMSS_ID={self.job.dmss_id}")
        envs.append(f"DMSS_URL={config.DMSS_API}")
        self.client.containers.run(
            image=full_image_name,
            command=custom_command,
            name=self.local_container_name,
            environment=envs,
            network="application_default",
            detach=True,
        )
        logger.info("*** Local container job started successfully ***")
        return "Ok"

    def remove(self) -> Tuple[str, str]:
        try:
            container = self.client.containers.get(self.local_container_name)
            container.remove()
        except docker.errors.NotFound:
            pass
        return JobStatus.REMOVED, "Removed"

    def progress(self) -> Tuple[JobStatus, str]:
        """Poll progress from the job instance"""
        if self.job.status == JobStatus.FAILED:
            # If setup fails, the container is not started
            return self.job.status, self.job.log
        try:
            container = self.client.containers.get(self.local_container_name)
            status = self.job.status
            if container.status == "running":
                status = JobStatus.RUNNING
            elif container.attrs["State"]["ExitCode"] >= 1:
                status = JobStatus.FAILED
            elif container.attrs["State"]["ExitCode"] == 0:
                status = JobStatus.COMPLETED
            logs = container.logs()
            return status, logs.decode()
        except docker.errors.NotFound as error:
            logger.error(f"Failed to poll progress of local container: {error}")
            return JobStatus.UNKNOWN, self.job.log

    def result(self) -> Tuple[str, bytes]:
        return "test 123", b"lkjgfdakljhfdgsllkjhldafgoiu8y03q987hgbloizdjhfpg980"
