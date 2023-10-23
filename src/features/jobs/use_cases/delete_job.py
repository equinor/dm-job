from uuid import UUID

from services.job_service import remove_job


def delete_job_use_case(job_id: str) -> str:
    result: str = remove_job(UUID(job_id))
    return result
