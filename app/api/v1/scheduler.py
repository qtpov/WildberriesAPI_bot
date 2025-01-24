from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import logging

scheduler = AsyncIOScheduler()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Прослушка событий для логирования успешных/неудачных выполнений задач
def job_listener(event):
    if event.exception:
        logging.error(f"Job {event.job_id} failed")
    else:
        logging.info(f"Job {event.job_id} executed successfully")

scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

# Запуск планировщика
scheduler.start()
