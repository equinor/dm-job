from pydantic.main import BaseModel

from services.job_handler_interface import JobStatus
from services.job_service import register_job


class StartJobResponse(BaseModel):
    uid: str
    message: str
    status: JobStatus


def start_job_use_case(job_dmss_id: str) -> StartJobResponse:
    uid, message, status = register_job(job_dmss_id)
    return StartJobResponse(uid=uid, message=message, status=status)
