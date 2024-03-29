import json
import os
from subprocess import Popen, STDOUT, PIPE, SubprocessError
from typing import TYPE_CHECKING, Optional, Any, List, Union
from zipfile import ZipFile

import psutil
from mcdreforged.api.types import Metadata, VersionRequirement
from parse import parse

from region_file_updater_multi.mcdr_globals import *
from region_file_updater_multi.upstream.abstract_upstream import AbstractUpstream
from region_file_updater_multi.utils.file_utils import RFUMFileNotFound
from region_file_updater_multi.utils.logging import get_pb_logger

if TYPE_CHECKING:
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti


_NONE = object()


class PrimeBackupProcessError(Exception):
    pass


class PrimeBackupFileNotFound(RFUMFileNotFound):
    pass


class NotAValidPrimeBackupArchive(SubprocessError):
    pass


class PrimeBackupUpstream(AbstractUpstream):
    __pb_check_error: Union[object, Exception, None] = _NONE

    @classmethod
    def assert_pb_valid(cls, rfum: "RegionFileUpdaterMulti"):
        def save_n_raise(exc: Exception):
            cls.__pb_check_error = exc
            raise exc

        if cls.__pb_check_error is not _NONE:
            if cls.__pb_check_error is None:
                return
            raise cls.__pb_check_error  # type: ignore[misc]

        def pb_invalid(exc: Optional[Any] = None):
            exc_str = "" if exc is None else f": {str(exc)}"
            save_n_raise(
                NotAValidPrimeBackupArchive(
                    f"Specified pb path is not a valid prime_backup plugin{exc_str}"
                )
            )

        pb_path = cls.get_pb_path(rfum)
        if pb_path is None or not os.path.isfile(pb_path):
            save_n_raise(FileNotFoundError("Prime backup is not found"))
        try:
            with ZipFile(pb_path, "r").open("mcdreforged.plugin.json") as f:
                meta = Metadata(json.load(f))
        except Exception as e:
            pb_invalid(e)
        if meta.id != PRIME_BACKUP_ID:
            pb_invalid(f"Metadata ID is {meta.id}")
        req = VersionRequirement(">=1.7.0")
        if not req.accept(meta.version):
            pb_invalid(
                f"Metadata version {meta.version} does not meet the requirement {req}"
            )

        cls.__pb_check_error = None

    @classmethod
    def assert_path_valid(cls, path: PathLike, rfum: "RegionFileUpdaterMulti"):
        cls.assert_pb_valid(rfum)
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        if not os.path.isfile(path):
            raise IsADirectoryError(path)
        if not os.path.splitext(path)[1] == ".db":
            raise ValueError("Not a db file path provided")

    @classmethod
    def get_pb_path(cls, rfum: "RegionFileUpdaterMulti"):
        return (
            rfum.config.paths.pb_plugin_package_path
            or rfum.server.get_plugin_file_path(PRIME_BACKUP_ID)
        )

    @classmethod
    def is_path_valid(cls, path: PathLike):
        return os.path.isfile(path) and os.path.splitext(path)[1] == ".db"

    def __init__(
        self, rfum: "RegionFileUpdaterMulti", name: str, file_path: str, world_name: str
    ):
        self.__rfum = rfum
        self.__name = name
        self.__path = file_path
        self.__world_name = world_name

    @property
    def name(self):
        return self.__name

    def parse_log_line(
        self,
        pattern: List[str],
        text: str,
        target_items: List[str],
        allow_not_found: bool = True,
    ):
        for p in pattern:
            result = parse(p, text)
            if result is not None:
                return_items = {}
                for item in target_items:
                    return_items[item] = result.named.get(item)
                if (
                    any([i is None for i in return_items.values()])
                    and not allow_not_found
                ):
                    continue
                if not any([i is not None for i in return_items.values()]):
                    continue
                return return_items
            self.__rfum.verbose(f"Not matched: {p}")
        return None

    def extract_file(
        self,
        file_name: PathLike,
        target_world_path: PathLike,
        enable_recycle: bool = True,
    ):
        if self.__rfum.server.is_on_executor_thread():
            raise RuntimeError(
                "Cannot invoke extract_file() on the task executor thread"
            )
        config = self.__rfum.config
        logger = get_pb_logger(
            self.__rfum.server,
            os.path.join(self.__rfum.get_data_folder(), CLI_STDOUT_LOG_FILE),
        )
        target_file_path = os.path.join(target_world_path, file_name)
        target_dir_path = os.path.dirname(target_file_path)
        self.__rfum.file_utilities.safe_ensure_dir(target_dir_path)
        if os.path.exists(target_file_path):
            self.__rfum.file_utilities.recycle(target_file_path)
        command = [
            config.get_python_executable(),
            self.get_pb_path(self.__rfum),
            "-d",
            self.__path,
            "extract",
            "latest",
            os.path.join(self.__world_name, file_name),
            "-o",
            target_dir_path,
        ]
        with Popen(command, stderr=STDOUT, stdout=PIPE, stdin=PIPE) as process:
            self.__rfum.verbose(f'Process started: {" ".join(command)}')
            decoding = (
                self.__rfum.config.get_popen_decoding()
                or self.__rfum.server.get_mcdr_config().get(MCDR_CFG_DECODING_KEY)
                or "utf8"
            )
            num = 0
            log_fmt = self.__rfum.config.get_pb_log_format()
            msg_fmt = self.__rfum.config.update_operation.prime_backup_file_not_found_log_format
            self.__rfum.verbose(f"Current parsing fmt: {log_fmt}")
            result = None
            while psutil.pid_exists(process.pid):
                num += 1
                if process.stdout is None:
                    continue
                try:
                    line_buf = next(iter(process.stdout))
                except StopIteration:
                    break
                else:
                    line_text = line_buf.decode(decoding).strip()
                    logger.info(line_text)
                    if result is None:
                        msg = self.parse_log_line(
                            log_fmt,
                            line_text,
                            [PrimeBackupLogParsingArguments.MSG.identifier],
                            allow_not_found=False,
                        )[PrimeBackupLogParsingArguments.MSG.identifier]
                        self.__rfum.verbose(f"Parsed message: {msg}")
                        if msg is None:
                            continue
                        # Target text: File 'world/level.data' in backup #4 does not exist
                        file_name_name = "file_name"
                        backup_id_name = "backup_id"
                        result = self.parse_log_line(
                            msg_fmt,
                            msg.strip(),
                            [file_name_name, backup_id_name],
                            allow_not_found=True,
                        )
                        self.__rfum.verbose(f"Parsed content: {result}")
                        if result is not None:
                            raise PrimeBackupFileNotFound(result.get(file_name_name))

        process.wait(self.__rfum.config.get_popen_terminate_timeout())
        if process.returncode != 0:
            raise PrimeBackupProcessError(f"Prime Backup returned {process.returncode}")
        if not os.path.isfile(target_file_path):
            raise PrimeBackupFileNotFound(
                "File not found after Prime Backup normal exits"
            )
