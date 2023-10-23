from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from config import config

jobstores = {
    "redis_job_store": RedisJobStore(
        db=0,
        host=config.SCHEDULER_REDIS_HOST,
        port=config.SCHEDULER_REDIS_PORT,
        password=config.SCHEDULER_REDIS_PASSWORD,
    )
}

scheduler = BackgroundScheduler(jobstores=jobstores, timezone="Etc/UTC")
scheduler.start()
