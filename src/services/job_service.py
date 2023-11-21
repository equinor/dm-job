from __future__ import annotations

import importlib
import json
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Tuple
from uuid import UUID, uuid4

import redis
from apscheduler.schedulers.background import BackgroundScheduler
from redis import AuthenticationError

from config import config
from restful.exceptions import (
    BadRequestException,
    NotFoundException,
    NotImplementedException,
)
from services.dmss import get_document, get_personal_access_token, update_document

# TODO: Authorization. The only level of authorization at this point is to allow all that
#  can view the job entity to also run and delete the job.
from services.job_handler_interface import Job, JobHandlerInterface, JobStatus
from services.job_scheduler import scheduler
from utils.logging import logger


def get_job_store():
    return redis.Redis(
        host=config.SCHEDULER_REDIS_HOST,
        port=config.SCHEDULER_REDIS_PORT,
        db=0,
        password=config.SCHEDULER_REDIS_PASSWORD,
        ssl=config.SCHEDULER_REDIS_SSL,
        socket_timeout=5,
        socket_connect_timeout=5,
    )


def schedule_cron_job(job_scheduler: BackgroundScheduler, function: Callable, job: Job) -> str:
    """Schedule a cron job.

    A cron job is a job that is run on a schedule. For example at 16:00 every Thursday.
    The cron syntax from unix is used to define when the job should run.
    For example: "30 12 * * 3" means that the job should run at 12:30 on Wednesday.

    It is assumed that the 'job' parameter contains an entity with a 'cron' string attribute that follows the cron syntax.
    """
    if not job.schedule:
        raise ValueError("CronJob entity is missing required attribute 'schedule'")
    try:
        minute, hour, day, month, day_of_week = job.schedule["cron"].split(" ")
        scheduled_job = job_scheduler.add_job(
            trigger="cron",
            func=function,
            args=[str(job.job_uid)],
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            id=str(job.job_uid),
            replace_existing=True,
            jobstore="redis_job_store",
        )
        return (
            "Cron job successfully registered. Next scheduled run "
            + f"at {scheduled_job.next_run_time} {scheduled_job.next_run_time.tzinfo}"
        )
    except ValueError as e:
        raise ValueError(f"Failed to schedule cron job '{job.job_uid}'. {e}'")


def _get_job(job_uid: UUID) -> Job:
    """Get a job from the job storage."""
    try:
        if raw_job := get_job_store().get(str(job_uid)):
            return Job(**json.loads(raw_job.decode()))
        else:
            raise NotFoundException(f"No job with id '{job_uid}' is registered")
    except AuthenticationError:
        raise ValueError(
            "Tried to fetch a job from Redis but no password"
            + " was supplied. Make sure SCHEDULER_REDIS_PASSWORD is set."
        )


def _set_job(job: Job):
    return get_job_store().set(str(job.job_uid), job.json())


def load_cron_jobs():
    for key in get_job_store().scan_iter():
        job = _get_job(UUID(key.decode()))
        if job.schedule:
            schedule_cron_job(scheduler, _run_job, job)
            logger.info(f"Loaded and registered job '{job.job_uid}' from {config.SCHEDULER_REDIS_HOST}")


def _get_job_handler(job: Job) -> JobHandlerInterface:
    """Get the job handler for a job.

    Job handlers must be placed in the "default_job_handlers" or the "job_handler_plugins" folder in the
    repository src folder.
    Each job handler have a folder with at least one file: __init__.py
    This __init__ file must implement a class called "JobHandler" that inherits from the JobHandlerInterface class.

    The runner type in the job entity (job.runner["type"]) decides what job handler to fetch.
    Also, the runner type must be equal to the '_SUPPORTED_TYPE' inside the job handler's __init__ file.
    """
    data_source_id = job.dmss_id.split("/", 1)[0]  # TODO use split_absolute_ref() to do this splitting.

    job_handler_directories = []
    for handler_location in ("default_job_handlers", "job_handler_plugins"):
        for file in Path(handler_location).iterdir():
            if file.is_dir() and file.name[0] != "_":  # Python modules can not start with "_"
                job_handler_directories.append(str(file).replace("/", "."))

    try:
        modules = [importlib.import_module(module) for module in job_handler_directories]
        for job_handler_module in modules:
            if job.runner["type"] == job_handler_module._SUPPORTED_TYPE:
                return job_handler_module.JobHandler(job, data_source_id)
    except ImportError as error:
        traceback.print_exc()
        raise ImportError(
            f"Failed to import a job handler module: '{error}'"
            + "Make sure the module has a '_init_.py' file, a 'JobHandler' class implementing "
            + "the JobHandlerInterface, and a global variable named '_SUPPORTED_TYPE' "
            + "with the string, tuple, or list value of the job type(s)."
        )

    raise NotImplementedError(f"No handler for a job of type '{job.runner['type']}' is configured")


def _run_job(job_uid: UUID) -> str:
    """Start a job, by calling the start() function for the job's job handler."""
    job: Job = _get_job(job_uid)
    try:
        job_handler = _get_job_handler(job)
        job.started = datetime.now()
        try:
            job.log = job_handler.start()
        except Exception as error:
            print(traceback.format_exc())
            logger.warning(f"Failed to run job; {job_uid}")
            job.status = JobStatus.FAILED
            raise error
    except NotImplementedError as error:
        job.log = (
            f"{job.log}\n\nThe jobHandler '{type(job_handler).__name__}' is missing some implementations: {error}"
        )
    except KeyError as error:
        job.log = (
            f"{job.log}\n\nThe jobHandler '{type(job_handler).__name__}' "
            f"tried to access a missing attribute: {error}"
        )
    except Exception as error:
        job.log = f"{job.log}\n\n{error}"
    finally:
        if job.type == config.RECURRING_JOB:
            # The recurring job has been updated within the JobHandler
            # Fetch the updated entity before merging data
            job.dmss_sync()

        update_document(
            job.dmss_id, job.json(by_alias=True, exclude_none=True, exclude=job.exclude_keys), job.token
        )  # Update in DMSS with status etc.

        _set_job(job)
        return job.log  # type: ignore


def register_job(dmss_id: str) -> Tuple[str, str]:
    """Register and start a job.

    Create an instance of the Job class from a job entity stored in DMSS, and start running the job.

    - **dmss_id**: address to the job entity to register. Can be on the formats:
      - By id: PROTOCOL://DATA SOURCE/$ID.Attribute
      - By path: PROTOCOL://DATA SOURCE/ROOT PACKAGE/SUB PACKAGE/ENTITY.Attribute
    """
    # A token must be created when there still is a request object.
    token = get_personal_access_token()
    job_entity = get_document(dmss_id, 0, token)
    kwargs = {
        "dmss_id": dmss_id,
        "job_uid": uuid4(),
        "started": datetime.now(),
        "token": token,
        **job_entity,
    }
    job = Job(**kwargs)
    _get_job_handler(job)  # Test for available handler before registering
    if job_entity.get("schedule"):
        job.status = JobStatus.REGISTERED
        result = str(job.job_uid), schedule_cron_job(
            scheduler,
            _run_job,
            job,
        )
    else:
        # Add a 5second delay on every job we run.
        # This is so that the JobService can update job state in
        # DMSS, before we get a race with the job itself trying to update it's state.
        in_5_seconds = datetime.now() + timedelta(seconds=5)
        job.status = JobStatus.STARTING
        scheduler.add_job(func=_run_job, next_run_time=in_5_seconds, args=[job.job_uid], jobstore="redis_job_store")
        result = str(job.job_uid), "Job successfully started"

    _set_job(job)
    update_document(job.dmss_id, job.json(by_alias=True, exclude_none=True, exclude=job.exclude_keys), token=job.token)
    return result


def status_job(job_uid: UUID) -> Tuple[JobStatus, str, str]:
    """Get the status for an existing job.

    The result of the job is fetched by using the progress() function in the job handler for the given job.
    """
    job = _get_job(job_uid)
    job_handler = _get_job_handler(job)
    try:
        status, log = job_handler.progress()
    except NotImplementedError:
        raise NotImplementedException(
            message="The job handler does not support the operation",
            debug="The job handler does not implement the 'progress' method",
        )
    job.status = status
    job.log = log

    _set_job(job)
    update_document(job.dmss_id, job.json(by_alias=True, exclude_none=True, exclude=job.exclude_keys), job.token)
    if job.schedule:
        cron_job = scheduler.get_job(str(job_uid), jobstore="redis_job_store")
        return status, job.log, f"Next scheduled run @ {cron_job.next_run_time} {cron_job.next_run_time.tzinfo}"
    return status, job.log, f"Started: {job.started.isoformat()}"


def remove_job(job_uid: UUID) -> str:
    """Remove an existing job.

    The remove() function in the job's job handler is used.
    Also, the job is removed from the job store.
    """
    job = _get_job(job_uid)
    job_handler = _get_job_handler(job)
    try:
        job_status, remove_message = job_handler.remove()
        job.status = job_status
    except NotImplementedError:
        raise NotImplementedException(
            message="The job handler does not support the operation",
            debug="The job handler does not implement the 'remove' method",
        )
    update_document(job.dmss_id, job.json(by_alias=True, exclude_none=True, exclude=job.exclude_keys), job.token)
    get_job_store().delete(str(job_uid))
    return remove_message  # type: ignore


def get_job_result(job_uid: UUID) -> Tuple[str, bytes]:
    """Get result from an existing job.

    The result() function in the job's job handler is used.
    """
    job = _get_job(job_uid)
    if not job.status.COMPLETED:
        raise BadRequestException("The job has not yet completed")
    job_handler = _get_job_handler(job)
    try:
        return job_handler.result()  # type: ignore
    except NotImplementedError:
        raise NotImplementedException(
            message="The job handler does not support the operation",
            debug="The job handler does not implement the 'result' method",
        )
