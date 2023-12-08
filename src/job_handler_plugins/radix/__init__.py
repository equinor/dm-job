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
        self.job_name = ""

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
        payload["DMSS_URL"] = config.DMSS_API
        payload["JOB_API_URL"] = config.JOB_API_URL
        payload["DMSS_ID"] = self.job.dmss_id
        result = requests.post(
            _get_job_url(self.job),
            json={"payload": json.dumps(payload)},
            timeout=10,
        )
        result.raise_for_status()
        # Need to store the unique job name in the state,
        # so that we can call the job scheduler
        # to get the progress or to remove the job.
        self.job.state = {"job_name": result.json()["name"]}
        return result.status_code  # type: ignore

    def remove(self) -> Tuple[JobStatus, str]:
        result = requests.delete(
            f"{_get_job_url(self.job)}/{self.job.state['job_name']}",
            timeout=10,
        )
        result.raise_for_status()
        return JobStatus.REMOVED, "Removed"

    def progress(self) -> Tuple[JobStatus, None | list[str] | str, None | float]:
        result = requests.get(
            f"{_get_job_url(self.job)}/{self.job.state['job_name']}",
            timeout=10,
        )
        result.raise_for_status()
        response_json = result.json()
        match (response_json["status"]):
            case "Running":  # noqa
                return JobStatus.RUNNING, "Job is running", None
            case "Failed":  # noqa
                return (
                    JobStatus.FAILED,
                    "Job failed for an unknown reason. Consider implementing job progress update for more details.",
                    0,
                )
            case "Succeeded":  # noqa
                return JobStatus.COMPLETED, "Radix job completed successfully", 1
            case _:
                return JobStatus.UNKNOWN, "Radix returned an unknown status code", 0
