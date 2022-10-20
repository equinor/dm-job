from typing import Tuple

import requests

from config import config
from services.job_handler_interface import Job, JobHandlerInterface, JobStatus
from utils.logging import logger

_SUPPORTED_TYPE = "WorkflowDS/Blueprints/ReverseDescription"


# TODO: Make a more realistic example with progress and a result file.
class JobHandler(JobHandlerInterface):
    """
    A silly test jobHandler that creates a NamedEntity of the input with it's description reversed
    """

    def __init__(self, job: Job, data_source: str):
        super().__init__(job, data_source)
        self.headers = {"Access-Key": job.token}

    def _get_by_id(self, document_id: str, depth: int = 1, attribute: str = ""):
        params = {"depth": depth, "attribute": attribute}
        req = requests.get(
            f"{config.DMSS_API}/api/v1/documents/{document_id}", params=params, headers=self.headers  # type: ignore
        )  # type: ignore
        req.raise_for_status()

        return req.json()

    def start(self) -> str:
        logger.info("Starting ReverseDescription job.")
        # input_entity = self._get_by_id(f"{self.data_source}/{self.job.entity['applicationInput']['_id']}")
        # result = input_entity.get("description", "")[::-1]
        logger.info("ReverseDescription job completed")
        return "OK"

    def result(self) -> Tuple[str, bytes]:
        return "Done", b"some value"

    def progress(self) -> Tuple[JobStatus, str]:
        return JobStatus.RUNNING, "50%"
