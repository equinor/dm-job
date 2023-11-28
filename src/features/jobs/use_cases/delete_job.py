from uuid import UUID

from pydantic.main import BaseModel

from services.job_handler_interface import JobStatus
from services.job_service import remove_job


class DeleteJobResponse(BaseModel):
    status: JobStatus
    response: str


def delete_job_use_case(job_id: UUID) -> DeleteJobResponse:
    status, res = remove_job(job_id)
    return DeleteJobResponse(status=status, response=res)
