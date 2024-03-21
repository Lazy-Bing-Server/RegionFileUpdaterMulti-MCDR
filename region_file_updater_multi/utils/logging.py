import logging
import os
import re

from mcdreforged.api.types import SyncStdoutStreamHandler, ServerInterface

from region_file_updater_multi.mcdr_globals import (
    PathLike,
    TRANSLATION_KEY_PREFIX,
    PB_LOGGER_NAME,
)


class NoColorFormatter(logging.Formatter):
    def formatMessage(self, record):
        return re.sub(r"\033\[(\d+(;\d+)?)?m", "", super().formatMessage(record))


def attach_file_handler(
    logger: logging.Logger,
    file_path: PathLike,
    formatter: logging.Formatter,
    encoding: str = "UTF-8",
):
    if not os.path.isfile(file_path):
        with open(file_path, "w") as f:
            f.write("")
    handler = logging.FileHandler(file_path, encoding=encoding)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return handler


def get_datetime_format(server: ServerInterface):
    key = f"{TRANSLATION_KEY_PREFIX}format.locale_datetime_fmt"
    return server.tr(key) if server.has_translation(key) else "%Y-%m-%d %H:%M:%S"


def get_time_format(server: ServerInterface):
    key = f"{TRANSLATION_KEY_PREFIX}format.locale_time_fmt"
    return server.tr(key) if server.has_translation(key) else "%H:%M:%S"


def get_pb_logger(server: ServerInterface, file_path: PathLike):
    logger = logging.Logger(PB_LOGGER_NAME)
    console_handler = SyncStdoutStreamHandler()
    console_handler.setFormatter(logging.Formatter("[%(name)s] %(message)s"))
    logger.addHandler(console_handler)
    attach_file_handler(logger, file_path, logging.Formatter("%(message)s"))
    return logger
