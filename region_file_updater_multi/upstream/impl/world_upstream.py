import os
from typing import TYPE_CHECKING
from pathlib import Path

from region_file_updater_multi.mcdr_globals import PathLike
from region_file_updater_multi.upstream.abstract_upstream import AbstractUpstream

if TYPE_CHECKING:
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti


class WorldSaveUpstream(AbstractUpstream):
    @classmethod
    def assert_path_valid(cls, path: PathLike, rfum: "RegionFileUpdaterMulti"):
        if not cls.is_path_valid(path):
            raise NotADirectoryError(path)

    def __init__(self, rfum: "RegionFileUpdaterMulti", name: PathLike, file_path: PathLike, world_name: str):
        self.__rfum = rfum
        self.__name = name
        self.__path = file_path
        self.__world_name = world_name

    @property
    def name(self):
        return self.__name

    @classmethod
    def is_path_valid(cls, path: PathLike):
        return os.path.isdir(path)

    def extract_file(self, file_name: PathLike, target_world_path: PathLike, enable_recycle: bool = True) -> None:
        original_path = Path(os.path.join(self.__path, self.__world_name, file_name)).resolve()
        target_path = os.path.join(target_world_path, file_name)
        self.__rfum.file_utilities.safe_ensure_dir(os.path.dirname(target_path))
        self.__rfum.file_utilities.copy(original_path, target_path, recycle_overwritten_file=enable_recycle)
