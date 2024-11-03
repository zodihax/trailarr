import collections
from datetime import datetime, timezone
import logging
import re
import aiofiles
from aiofiles import os as async_os
import os
from fastapi import APIRouter

from api.v1.models import Log
from config.settings import app_settings


logs_router = APIRouter(prefix="/logs", tags=["Logs"])


@logs_router.get("/")
async def get_logs(page: int = 1, limit: int = 100) -> list[Log]:
    # Read logs from file and send it back
    logs_dir = os.path.abspath(os.path.join(app_settings.app_data_dir, "logs"))
    # logs: list[str] = []
    logs: collections.deque = collections.deque(maxlen=limit)
    if not await async_os.path.exists(logs_dir):
        logging.info("Logs directory does not exist")
        return [
            Log(
                datetime=f"{datetime.now(timezone.utc)}",
                level="INFO",
                filename="Other",
                lineno=1,
                module="Other",
                message="No Logs Found",
                raw_log="No Logs Found",
            )
        ]
    for log_file in await async_os.listdir(logs_dir):
        if log_file.endswith(".log"):
            # logging.info(f"Reading logs from {log_file}")
            # with open(f"{logs_dir}/{log_file}", "r") as f:
            #     for line in f:
            #         logs.append(line)
            file = await aiofiles.open(f"{logs_dir}/{log_file}", mode="r")
            async for line in file:
                loggg = convert_log(line)
                logs.append(loggg)

    logs.reverse()
    return list(logs)
    # logs_filtered = logs[(page - 1) * limit : page * limit]
    # return logs_filtered


LOG_REGEX = re.compile(
    r"^(?P<datetime>[^\s]+)\s\[(?P<level>[^\|]+)\|(?P<filename>[^\|]+)\|L(?P<lineno>\d+)\]"
    r":\s(?P<message>.*)$"
)
LOG_MSG_REGEX = re.compile(r"^(?P<module>[\w]+):\s(?P<message>.*)$")


def convert_log(log: str) -> Log:
    match_log = LOG_REGEX.search(log)
    if match_log:
        module = "Other"
        message = match_log.group("message")
        match_module = LOG_MSG_REGEX.search(message)
        if message.lower().startswith("job"):
            module = "Tasks"
        if match_module:
            module = match_module.group("module")
            message = match_module.group("message")
        log_obj = Log(
            datetime=match_log.group("datetime"),
            level=match_log.group("level"),
            filename=match_log.group("filename"),
            lineno=int(match_log.group("lineno")),
            module=module,
            message=message,
            raw_log=log,
        )
        return log_obj
    return Log(
        datetime=f"{datetime.now(timezone.utc)}",
        level="INFO",
        filename="Other",
        lineno=1,
        module="Other",
        message=log,
        raw_log=log,
    )
