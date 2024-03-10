import json
import os
import subprocess
import sys

from typing import TYPE_CHECKING, Optional, Any
from zipfile import ZipFile

import psutil
from mcdreforged.api.types import SyncStdoutStreamHandler, Metadata, VersionRequirement
from mcdreforged.api.rtext import *

from region_file_updater_multi.mcdr_globals import PathLike, CLI_STDOUT_LOG_FILE
from region_file_updater_multi.upstream.abstract_upstream import AbstractUpstream
from region_file_updater_multi.mcdr_globals import PRIME_BACKUP_ID, MCDR_CFG_DECODING_KEY
from region_file_updater_multi.utils.logging import get_pb_logger
from subprocess import Popen, STDOUT, PIPE, check_output

if TYPE_CHECKING:
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti
    from region_file_updater_multi.region import Region


_NONE = object()


class PrimeBackupProcessError(Exception):
    pass


class NotAValidPrimeBackupArchive(ValueError):
    pass


class PrimeBackupUpstream(AbstractUpstream):
    __pb_check_error = _NONE

    @classmethod
    def assert_pb_valid(cls, rfum: "RegionFileUpdaterMulti"):
        def save_n_raise(exc: Exception):
            cls.__pb_check_error = exc
            raise exc

        if cls.__pb_check_error is not _NONE:
            if cls.__pb_check_error is None:
                return
            raise cls.__pb_check_error

        def pb_invalid(exc: Optional[Any] = None):
            exc_str = '' if exc is None else f': {str(exc)}'
            save_n_raise(NotAValidPrimeBackupArchive(f"Specified pb path is not a valid prime_backup plugin{exc_str}"))
        pb_path = cls.get_pb_path(rfum)
        if pb_path is None or not os.path.isfile(pb_path):
            save_n_raise(FileNotFoundError("Prime backup is not found"))
        try:
            with ZipFile(pb_path, 'r').open('mcdreforged.plugin.json') as f:
                meta = Metadata(json.load(f))
        except Exception as e:
            pb_invalid(e)
        if meta.id != PRIME_BACKUP_ID:
            pb_invalid(f'Metadata ID is {meta.id}')
        req = VersionRequirement('>=1.7.0')
        if not req.accept(meta.version):
            pb_invalid(f'Metadata version {meta.version} does not meet the requirement {req}')

        cls.__pb_check_error = None

    @classmethod
    def assert_path_valid(cls, path: PathLike, rfum: "RegionFileUpdaterMulti"):
        cls.assert_pb_valid(rfum)
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        if not os.path.isfile(path):
            raise IsADirectoryError(path)
        if not path.endswith('.db'):
            raise ValueError('Not a db file path provided')

    def __init__(self, rfum: "RegionFileUpdaterMulti", name: str, file_path: str, world_name: str):
        self.__rfum = rfum
        self.__name = name
        self.__path = file_path
        self.__world_name = world_name

    @property
    def name(self):
        return self.__name

    def extract_file(self, file_name: PathLike, target_world_path: PathLike, enable_recycle: bool = True) -> None:
        if self.__rfum.server.is_on_executor_thread():
            raise RuntimeError('Cannot invoke extract_file() on the task executor thread')
        config = self.__rfum.config
        logger = get_pb_logger(self.__rfum.server, os.path.join(self.__rfum.get_data_folder(), CLI_STDOUT_LOG_FILE))
        target_file_path = os.path.join(target_world_path, file_name)
        target_dir_path = os.path.dirname(target_file_path)
        self.__rfum.file_utilities.safe_ensure_dir(target_dir_path)
        if os.path.exists(target_file_path):
            self.__rfum.file_utilities.recycle(target_file_path)
        command = [
            config.get_python_executable(),
            self.get_pb_path(self.__rfum),
            '-d', self.__path,
            'extract', 'latest', os.path.join(self.__world_name, file_name),
            '-o', target_dir_path
        ]
        process = Popen(command, stderr=STDOUT, stdout=PIPE, stdin=PIPE)
        logger.info(f'Process started: {" ".join(command)}')
        num = 0
        while psutil.pid_exists(process.pid):
            num += 1
            try:
                line_buf = next(iter(process.stdout))
            except StopIteration:
                break
            else:
                decoding = self.__rfum.config.get_popen_decoding() or self.__rfum.server.get_mcdr_config().get(MCDR_CFG_DECODING_KEY) or 'utf8'
                line_text = line_buf.decode(decoding)
                logger.info(line_text.strip())
        process.wait(3)
        if process.returncode != 0:
            raise PrimeBackupProcessError(f"Prime Backup returned {process.returncode}")
        if not os.path.isfile(target_file_path):
            raise PrimeBackupProcessError("File not found after Prime Backup normal exits")

    @classmethod
    def get_pb_path(cls, rfum: "RegionFileUpdaterMulti"):
        return rfum.config.paths.pb_plugin_package_path or rfum.server.get_plugin_file_path(PRIME_BACKUP_ID)

    @classmethod
    def is_path_valid(cls, path: PathLike):
        return os.path.isfile(path) and path.endswith('.db')

