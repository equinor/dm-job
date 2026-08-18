import json
from typing import Tuple

import requests

from config import config
from services.job_handler_interface import Job, JobHandlerInterface, JobStatus
from utils.logging import logger

_SUPPORTED_TYPE = "dmss://WorkflowDS/Blueprints/Radix"


def _get_job_url(job: Job) -> str:
    job_name: str = job.runner["jobName"]
    scheduler_port: str = job.runner["schedulerPort"]
    return f"http://{job_name}:{scheduler_port}/api/v1/jobs"


def list_of_env_to_dict(env_vars: list[str]) -> dict:
    return {s.split("=", 1)[0]: s.split("=", 1)[1] for s in env_vars}


class JobHandler(JobHandlerInterface):
    def __init__(self, job: Job, data_source: str):
        super().__init__(job, data_source)

    def start(self) -> str:
        logger.info("Starting Radix job...")
        # Add token and URL to payload, so that jobs are able to connect to the DMSS instance.
        try:
            payload = list_of_env_to_dict(self.job.runner.get("environmentVariables", []))
        except IndexError:
            raise ValueError(
                f"Malformed environment variable received by job handler of type {_SUPPORTED_TYPE}. Should be on the format <key>=<value> (location: {self.job.dmss_id})"
            )
        payload["DMSS_TOKEN"] = self.job.token
        payload["DMSS_URL"] = config.DMSS_URL
        payload["DM_JOB_URL"] = config.DM_JOB_URL
        payload["JOB_DMSS_ID"] = self.job.dmss_id

        # Optional per-submission override of the Radix component's image tag.
        # The template's 'image' must contain '{imageTagName}' for this to take effect;
        # if the runner omits it, Radix falls back to the default in radixconfig.yaml.
        body: dict = {"payload": json.dumps(payload)}
        if image_tag := self.job.runner.get("imageTagName"):
            body["imageTagName"] = image_tag

        result = requests.post(
            _get_job_url(self.job),
            json=body,
            timeout=10,
        )
        result.raise_for_status()
        # Need to store the unique job name in the state,
        # so that we can call the job scheduler
        # to get the progress or to remove the job.
        self.job.state = {"job_name": result.json()["name"]}
        return str(result.status_code)

    def remove(self) -> Tuple[JobStatus, str]:
        if not self.job.state:
            return JobStatus.REMOVED, "Removed"

        result = requests.delete(
            f"{_get_job_url(self.job)}/{self.job.state['job_name']}",
            timeout=10,
        )
        result.raise_for_status()
        return JobStatus.REMOVED, "Removed"

    def progress(self) -> Tuple[JobStatus, None | list[str] | str, None | float]:
        if self.job.status == JobStatus.FAILED:
            return JobStatus.FAILED, self.job.log, None
        if not self.job.state:
            return self.job.status, "Radix job is not running yet.", 0
        result = requests.get(
            f"{_get_job_url(self.job)}/{self.job.state['job_name']}",
            timeout=10,
        )
        result.raise_for_status()
        response_json = result.json()
        # Radix batch-job scheduler statuses:
        #   Waiting   - pod scheduled, pulling image / waiting for a node
        #   Active    - job resource created, first pod not yet Running
        #   Running   - container process is up
        #   Succeeded - terminal, exit 0
        #   Failed    - terminal, non-zero exit or runtime failure
        #   Stopping  - kubectl delete in progress after a stop request
        #   Stopped   - terminated by an operator/user
        #   DeadlineExceeded - killed because activeDeadlineSeconds elapsed
        # Anything else is a genuine surprise and stays UNKNOWN.
        match (response_json.get("status")):
            case "Running":  # noqa
                return JobStatus.RUNNING, "Job is running", None
            case "Waiting" | "Active":  # noqa - image pull / node scheduling
                return JobStatus.STARTING, "Radix job is starting (pod scheduling / image pull)", 0
            case "Failed":  # noqa
                return (
                    JobStatus.FAILED,
                    "Job failed for an unknown reason. Consider implementing job progress update for more details.",
                    0,
                )
            case "Stopping" | "Stopped":  # noqa - operator-initiated termination
                return JobStatus.FAILED, "Radix job was stopped", 0
            case "DeadlineExceeded":  # noqa
                return JobStatus.FAILED, "Radix job exceeded its active deadline", 0
            case "Succeeded":  # noqa
                return JobStatus.COMPLETED, "Radix job completed successfully", 1
            case None:
                return JobStatus.STARTING, "Radix job is starting", 1
            case unknown:
                logger.warning(f"Radix returned an unmapped job status: {unknown!r}")
                return JobStatus.UNKNOWN, f"Radix returned an unknown status: {unknown}", 0
