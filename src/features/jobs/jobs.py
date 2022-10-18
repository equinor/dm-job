from fastapi import APIRouter
from starlette.responses import JSONResponse, PlainTextResponse

from features.jobs.use_cases.delete_job import delete_job_use_case
from features.jobs.use_cases.get_result_job import (
    GetJobResultResponse,
    get_job_result_use_case,
)
from features.jobs.use_cases.start_job import StartJobResponse, start_job_use_case
from features.jobs.use_cases.status_job import StatusJobResponse, status_job_use_case
from restful.responses import create_response

router = APIRouter()


@router.post("/{job_dmss_id:path}", operation_id="start_job", response_model=StartJobResponse)
@create_response(JSONResponse)
def start(job_dmss_id: str):
    return start_job_use_case(job_dmss_id=job_dmss_id).dict()


@router.get("/{job_uid}", operation_id="job_status", response_model=StatusJobResponse)
@create_response(JSONResponse)
def status(job_uid: str):
    return status_job_use_case(job_id=job_uid).dict()


@router.delete("/{job_uid}", operation_id="remove_job")
@create_response(PlainTextResponse)
def remove(job_uid: str):
    return delete_job_use_case(job_id=job_uid)


@router.get("/{job_uid}/result", operation_id="job_result", response_model=GetJobResultResponse)
@create_response(JSONResponse)
def result(job_uid: str):
    return get_job_result_use_case(job_uid=job_uid).dict()
