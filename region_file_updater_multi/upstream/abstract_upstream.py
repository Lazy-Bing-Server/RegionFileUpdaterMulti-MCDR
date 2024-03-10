from abc import ABC, abstractmethod

from typing import TYPE_CHECKING, Union, Iterable, Tuple, Optional
from region_file_updater_multi.mcdr_globals import PathLike
from mcdreforged.api.rtext import RColor, RStyle
from region_file_updater_multi.mcdr_globals import MessageText


if TYPE_CHECKING:
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti


class AbstractUpstream(ABC):
    @abstractmethod
    def __init__(self, rfum: "RegionFileUpdaterMulti", name: str, file_path: str, world_name: str):
        ...

    @property
    @abstractmethod
    def name(self):
        ...

    @abstractmethod
    def extract_file(self, file_name: PathLike, target_world_path: PathLike, enable_recycle: bool = True) -> None:
        """
        Extract file to target world save path
        :param file_name: File in upstream file
        :param target_world_path: The path of the target world save folder
        :param enable_recycle: Enable this flag to disable auto recycles during extract
        :return: None
        """
        ...

    # Deprecated
    @classmethod
    @abstractmethod
    def is_path_valid(cls, path: PathLike):
        ...

    @classmethod
    @abstractmethod
    def assert_path_valid(cls, path: PathLike, rfum: "RegionFileUpdaterMulti"):
        ...
