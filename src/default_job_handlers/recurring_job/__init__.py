from datetime import datetime, timezone
from typing import Tuple

from services.dmss import add_document
from services.job_handler_interface import Job, JobHandlerInterface, JobStatus
from services.job_service import register_job, remove_job
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

    def start(self) -> str:
        current_date = datetime.now(timezone.utc)
        if datetime.fromisoformat(self.job.schedule["startDate"]) > current_date:
            msg = f"Job is not valid yet, and will run for the first time after {self.job.schedule['startDate']}."
            logger.info(msg)
            return msg
        elif datetime.fromisoformat(self.job.schedule["endDate"]) <= current_date:
            remove_job(self.job.job_uid)
            msg = f"Recurring job {self.job.job_uid} has expired since {self.job.schedule['endDate']}. Removing..."
            logger.info(msg)
            return msg

        msg = f'Starting scheduled job from "{self.job.dmss_id}"'
        logger.info(msg)
        self.job.append_log(msg)
        job_template = self.job.application_input
        actual_app_input_address = job_template["applicationInput"]["address"]
        # Relative references will be wrong when we move the template into "schedule.runs"
        if actual_app_input_address[0] == "~":
            job_template["applicationInput"]["address"] = f"~.{actual_app_input_address}"
        new_job_address = add_document(f"{self.job.dmss_id}.schedule.runs", job_template, self.job.token)
        # TODO: Update DMSS to return complete address, and avoid this ugly stuff
        complete_new_job_address = self.job.dmss_id.split("$", 1)[0] + "$" + new_job_address["uid"]
        new_uid, new_log, status = register_job(complete_new_job_address, self.job.token)

        msg = f'Job: "{new_uid}", Status: "{status}"'
        logger.info(msg)
        self.job.append_log(msg)
        return msg

    def remove(self) -> Tuple[JobStatus, str]:
        """Terminate and cleanup all job related resources"""
        return JobStatus.REMOVED, "OK. Nothing to clean up"

    def result(self) -> Tuple[str, bytes]:
        raise NotImplementedError

    def progress(self) -> Tuple[JobStatus, None | list[str] | str, None | float]:
        return self.job.status, self.job.log, self.job.percentage
