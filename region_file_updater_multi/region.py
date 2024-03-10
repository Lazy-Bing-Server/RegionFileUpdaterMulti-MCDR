import enum
import os
import threading
from typing import Iterable, TYPE_CHECKING, Union, Dict, Optional, Type, Tuple
from dataclasses import dataclass

from region_file_updater_multi.upstream.abstract_upstream import AbstractUpstream
from region_file_updater_multi.upstream.impl.world_upstream import WorldSaveUpstream
from region_file_updater_multi.upstream.impl.pb_upstream import PrimeBackupUpstream
from region_file_updater_multi.upstream.impl.invalid_upstream import InvalidUpstream


if TYPE_CHECKING:
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti
    from region_file_updater_multi.config import Config
    from typing import Literal


@dataclass(unsafe_hash=False)
class Region:
    x: int
    z: int
    dim: str

    @classmethod
    def from_player_coordinates(cls, x: float, z: float, dim: str):
        return cls(int(x) // 512, int(z) // 512, dim)

    def to_file_name(self):
        return 'r.{}.{}.mca'.format(self.x, self.z)

    def to_file_list(self, config: "Config"):
        file_list = []
        folders = config.paths.dimension_region_folder[str(self.dim)]
        if isinstance(folders, str):
            file_list.append(os.path.join(folders, self.to_file_name()))
        elif isinstance(folders, Iterable):
            for folder in folders:
                file_list.append(os.path.join(folder, self.to_file_name()))
        else:
            pass
        return file_list

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.x == other.x and self.z == other.z and self.dim == other.dim


class UpstreamType(enum.Enum):
    world = WorldSaveUpstream
    prime_backup = PrimeBackupUpstream


class RegionUpstreamManager:
    __instance: Optional['RegionUpstreamManager'] = None

    @classmethod
    def get_instance(cls, rfum: Optional['RegionFileUpdaterMulti'] = None):
        if not isinstance(cls.__instance, cls):
            if rfum is None:
                raise RuntimeError("Create instance failed")
            cls.__instance = cls(rfum)
        return cls.__instance

    def __init__(self, rfum: "RegionFileUpdaterMulti"):
        self.__rfum = rfum
        self.__upstream: Dict[str, "AbstractUpstream"] = {}
        self.__lock = threading.RLock()

        if self.__rfum.config.paths.upstreams is None:
            return
        for name, upstream_info in self.__rfum.config.paths.upstreams.items():
            cls: Type["AbstractUpstream"] = UpstreamType[upstream_info.type].value
            try:
                cls.assert_path_valid(upstream_info.path, self.__rfum)
                self.__upstream[name] = cls(rfum, name, upstream_info.path, upstream_info.world_name)
            except Exception as exc:
                self.__upstream[name] = InvalidUpstream(rfum, name, upstream_info.path, upstream_info.world_name).set_error_message(cls, exc)

    @property
    def upstreams(self):
        return self.__upstream

    def get_sorted_upstreams(self) -> Iterable[Tuple[str, AbstractUpstream]]:
        with self.__lock:
            return sorted(self.upstreams.items(), key=lambda item: item[0])

    def get_current_upstream(self):
        return self.__upstream.get(self.__rfum.config.paths.current_upstream)

    def get_upstream_name_suggester(self):
        return lambda: self.__upstream.keys()

    def get_upstream_name_checker(self, node_name: str):
        return lambda src, ctx: ctx[node_name] in self.__upstream.keys(), \
            lambda src, ctx: self.__rfum.rtr('command.upstream.error.not_found', ctx[node_name])

    def set_current_upstream(self, upstream_name: str):
        if upstream_name not in self.__upstream.keys():
            raise KeyError(upstream_name)
        self.__rfum.config.paths.current_upstream = upstream_name
        self.__rfum.save_config()

    def get_required_file_list(self, region: "Region"):
        return region.to_file_list(self.__rfum.config)

    def extract_region_files(self, region: "Region"):
        with self.__lock:
            file_list = region.to_file_list(self.__rfum.config)
            for file in file_list:
                self.get_current_upstream().extract_file(file, self.__rfum.config.paths.destination_world_directory)
