import json
from typing import Tuple

import requests

from config import config
from services.job_handler_interface import Job, JobHandlerInterface, JobStatus
from utils.logging import logger

_SUPPORTED_TYPE = "dmss://WorkflowDS/Blueprints/Radix"


def _get_job_url(job: Job) -> str:
    job_name: str = job.entity["runner"]["jobName"]
    scheduler_port: str = job.entity["runner"]["schedulerPort"]
    return f"http://{job_name}:{scheduler_port}/api/v1/jobs"


class JobHandler(JobHandlerInterface):
    def __init__(self, job: Job, data_source: str):
        super().__init__(job, data_source)
        self.job_name = ""

    def start(self) -> str:
        logger.info("Starting Radix job...")
        # Add token and URL to payload, so that jobs are able to connect to the DMSS instance.
        payload = {"DMSS_TOKEN": self.job.token, "DMSS_URL": config.DMSS_API}
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
        return result.status()  # type: ignore

    def remove(self) -> Tuple[str, str]:
        result = requests.delete(
            f"{_get_job_url(self.job)}/{self.job.state['job_name']}",
            timeout=10,
        )
        result.raise_for_status()
        return JobStatus.REMOVED, "Removed"

    def progress(self) -> Tuple[JobStatus, str]:
        result = requests.get(
            f"{_get_job_url(self.job)}/{self.job.state['job_name']}",
            timeout=10,
        )
        result.raise_for_status()
        response_json = result.json()
        job_status = JobStatus.UNKNOWN
        match (response_json["status"]):  # noqa
            case "Running":  # noqa
                job_status = JobStatus.RUNNING
            case "Failed":  # noqa
                job_status = JobStatus.FAILED
            case "Succeeded":  # noqa
                job_status = JobStatus.COMPLETED
        return job_status, response_json["message"]