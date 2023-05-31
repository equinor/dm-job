import os
from pathlib import Path
from typing import Tuple

import requests

from config import config
from services.job_handler_interface import Job, JobHandlerInterface, JobStatus
from utils.logging import logger

_SUPPORTED_TYPE = "dmss://WorkflowDS/Blueprints/ReverseDescription"


# TODO: Make a more realistic example with progress and a result file.
class JobHandler(JobHandlerInterface):
    """
    A silly test jobHandler that creates a NamedEntity of the input with it's description reversed
    """

    results_directory = f"{Path(__file__).parent}/results"
    os.makedirs(results_directory, exist_ok=True)

    def __init__(
        self,
        job: Job,
        data_source: str,
    ):
        super().__init__(job, data_source)
        self.headers = {"Access-Key": job.token}

    def _get_by_id(self, reference: str, depth: int = 1, attribute: str = ""):
        params = {"depth": depth, "attribute": attribute}
        req = requests.get(
            f"{config.DMSS_API}/api/documents/{reference}?resolve_links=true&depth=100", params=params, headers=self.headers  # type: ignore
        )  # type: ignore
        req.raise_for_status()
        return req.json()

    def start(self) -> str:
        logger.info("Starting ReverseDescription job.")
        input_entity = self._get_by_id(f"{self.data_source}/${self.job.entity['applicationInput']['_id']}")
        result = input_entity.get("description", "Backup")[::-1]
        with open(f"{self.results_directory}/{self.job.job_uid}", "w") as result_file:
            result_file.write(result)
        logger.info("ReverseDescription job completed")
        return "OK"

    def result(self) -> Tuple[str, bytes]:
        result_file_path = Path(f"{self.results_directory}/{self.job.job_uid}")
        if not result_file_path.is_file():
            return "No result file found", b""

        with open(result_file_path, "rb") as result_file:
            return "Done", result_file.read()

    def progress(self) -> Tuple[JobStatus, str]:
        return self.job.status, "Progress tracking not implemented"
