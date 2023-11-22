from typing import Tuple

from services.dmss import add_document
from services.job_handler_interface import Job, JobHandlerInterface, JobStatus
from services.job_service import register_job
from utils.logging import logger

_SUPPORTED_TYPE = "dmss://WorkflowDS/Blueprints/RecurringJobHandler"


class JobHandler(JobHandlerInterface):
    """
    Job handler for RecurringJob.
    RecurringJobs must have a schedule, and the "applicationInput" must be of type "Job".
    This handler will then create a new Job entity everytime this job runs, and start it.
    """

    def __init__(
        self,
        job: Job,
        data_source: str,
    ):
        super().__init__(job, data_source)
        self.headers = {"Access-Key": job.token or ""}

    def start(self) -> str:
        msg = f'Starting scheduled job from "{self.job.dmss_id}"'
        logger.info(msg)
        self.job.append_log(msg)

        job_template = self.job.application_input
        new_job_address = add_document(f"{self.job.dmss_id}.schedule.runs", job_template, self.job.token)
        # TODO: Update DMSS to return complete address, and avoid this ugly stuff
        complete_new_job_address = self.job.dmss_id.split("$", 1)[0] + "$" + new_job_address["uid"]

        new_uid, new_log = register_job(complete_new_job_address)

        msg = f'Job: "{new_uid}", Status: "{new_log}"'
        logger.info(msg)
        self.job.append_log(msg)
        self.job.status = JobStatus.RUNNING
        return "OK"

    def remove(self) -> str:
        """Terminate and cleanup all job related resources"""
        raise NotImplementedError

    def result(self) -> Tuple[str, bytes]:
        raise NotImplementedError

    def progress(self) -> Tuple[JobStatus, None | list[str], None | str]:
        return self.job.status, self.job.log, None
