import json
import os.path
import threading
from typing import TYPE_CHECKING, List, Optional, overload, Iterable, Dict, Union

from mcdreforged.api.all import *

from region_file_updater_multi.utils.serializer import RFUMSerializable
from region_file_updater_multi.region import Region
from region_file_updater_multi.mcdr_globals import CommandCallback


if TYPE_CHECKING:
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti


class GroupFileData(RFUMSerializable):
    name: str = ""
    regions: List[Region] = []
    protect_regions_from_update: bool = False
    enable_whitelist: bool = False
    whitelist: List[str] = []
    enable_blacklist: bool = False
    blacklist: List[str] = []


class Group:
    def __init__(
        self,
        data: "GroupFileData",
        group_manager: "GroupManager",
        lock: Optional[threading.RLock] = None,
    ):
        self.__manager = group_manager
        self.__data = data
        self.__lock = lock or threading.RLock()

    @property
    def name(self):
        return self.__data.name

    @property
    def regions(self):
        return self.__data.regions

    @property
    def whitelisted_players(self):
        return self.__data.whitelist

    @property
    def blacklisted_players(self):
        return self.__data.blacklist

    @property
    def is_present(self):
        return self.__manager.is_present(self)

    @property
    def is_protection_enabled(self):
        return self.__data.protect_regions_from_update

    @property
    def is_whitelist_enabled(self):
        return self.__data.enable_whitelist

    @property
    def is_blacklist_enabled(self):
        return self.__data.enable_blacklist

    def add_region(self, region: "Region"):
        with self.__lock:
            if self.is_listed(region):
                return False
            self.regions.append(region)
            return self.save()

    def remove_region(self, region: "Region"):
        with self.__lock:
            if not self.is_listed(region):
                return False
            self.regions.remove(region)
            return self.save()

    def is_listed(self, region: "Region"):
        with self.__lock:
            return region in self.regions

    def get_data(self, group_manager: "GroupManager"):
        with self.__lock:
            if group_manager is self.__manager:
                return self.__data
            return None

    def save(self):
        with self.__lock:
            return self.__manager.save()

    @classmethod
    def new(
        cls,
        name: str,
        group_manager: "GroupManager",
        lock: Optional[threading.RLock] = None,
    ):
        return cls(
            GroupFileData.deserialize(dict(name=name)),
            group_manager=group_manager,
            lock=lock,
        )

    def is_player_whitelisted(self, player: str):
        with self.__lock:
            return player in self.__data.whitelist

    def is_player_blacklisted(self, player: str):
        with self.__lock:
            return player in self.__data.blacklist

    def is_src_permitted(self, source: CommandSource):
        with self.__lock:
            if not isinstance(source, PlayerCommandSource):
                return True
            if not self.__data.protect_regions_from_update:
                return True
            return self.is_player_whitelisted(
                source.player
            ) and not self.is_player_blacklisted(source.player)


class GroupManager:
    def __init__(self, path: str, rfum: "RegionFileUpdaterMulti"):
        self.__lock = threading.RLock()
        self.__path = path
        self.__rfum = rfum
        self.__groups: Dict[str, Group] = {}
        self.load()

    def is_present(self, group: Union[str, Group]):
        with self.__lock:
            if isinstance(group, str):
                group = self.get_group(group)
            return isinstance(group, Group) and group in self.__groups.keys()

    def get_group_suggester(self) -> CommandCallback[Iterable[str]]:
        def suggester():
            return self.__groups.keys()

        return suggester

    def load(self) -> bool:
        with self.__lock:
            self.__groups = {}
            try:
                with open(self.__path, "r", encoding="utf8") as f:
                    data_list = deserialize(json.load(f), List[GroupFileData])
            except FileNotFoundError:
                self.save()
                return True
            except (KeyError, ValueError):
                self.__rfum.logger.exception("Loading group file failed")
                self.save()
                return False
            for item in data_list:
                self.__groups[item.name] = Group(item, self, self.__lock)
            return True

    def save(self) -> bool:
        with self.__lock:
            data_list = [group.get_data(self) for group in self.__groups.values()]
            if os.path.isdir(self.__path):
                os.removedirs(self.__path)
            try:
                with open(self.__path, "w", encoding="utf8") as f:
                    json.dump(serialize(data_list), f, ensure_ascii=False, indent=4)
            except (KeyError, ValueError):
                self.__rfum.logger.exception("Saving group file failed")
                return False
            return True

    def get_group(self, name: str):
        with self.__lock:
            return self.__groups.get(name)

    def create_group(self, name: str):
        with self.__lock:
            if name in self.__groups.keys():
                return None
            self.__groups[name] = Group.new(name, self, self.__lock)
            if self.save():
                return self.__groups[name]
            return None

    def delete_group(self, name: str):
        with self.__lock:
            target_group = self.__groups.pop(name, None)
            if target_group is None:
                return None
            if self.save():
                return target_group
            return None

    def get_group_by_region(self, region: Region) -> Iterable[Group]:
        for group in self.__groups.values():
            if group.is_listed(region):
                yield group

    def is_region_permitted(self, source: CommandSource, region: Region):
        return all(
            [
                group.is_src_permitted(source)
                for group in self.get_group_by_region(region)
            ]
        )
