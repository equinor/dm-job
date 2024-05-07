from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from config import config

jobstores = {
    "redis_job_store": RedisJobStore(
        db=6,  # DMSS is using 0-3
        host=config.SCHEDULER_REDIS_HOST,
        port=config.SCHEDULER_REDIS_PORT,
        password=config.SCHEDULER_REDIS_PASSWORD,
        ssl=config.SCHEDULER_REDIS_SSL,
    )
}

scheduler = BackgroundScheduler(jobstores=jobstores, timezone="Etc/UTC")
scheduler.start()
