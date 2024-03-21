from abc import ABC, abstractmethod

from typing import TYPE_CHECKING
from region_file_updater_multi.mcdr_globals import PathLike


if TYPE_CHECKING:
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti


class AbstractUpstream(ABC):
    # Deprecated
    @classmethod
    @abstractmethod
    def is_path_valid(cls, path: PathLike): ...

    @classmethod
    @abstractmethod
    def assert_path_valid(cls, path: PathLike, rfum: "RegionFileUpdaterMulti"): ...

    @abstractmethod
    def __init__(
        self, rfum: "RegionFileUpdaterMulti", name: str, file_path: str, world_name: str
    ): ...

    @property
    @abstractmethod
    def name(self): ...

    @abstractmethod
    def extract_file(
        self,
        file_name: PathLike,
        target_world_path: PathLike,
        enable_recycle: bool = True,
    ) -> None: ...
