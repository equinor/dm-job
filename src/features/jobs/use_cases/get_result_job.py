from uuid import UUID

from pydantic import BaseModel

from services.job_service import get_job_result


class GetJobResultResponse(BaseModel):
    message: str
    result: str


def get_job_result_use_case(job_uid: UUID) -> GetJobResultResponse:
    message, bytesvalue = get_job_result(job_uid)
    return GetJobResultResponse(message=message, result=bytesvalue)
