import contextlib
import json
import os.path
import threading
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, List, Optional, Iterable, Dict, Union, TypeVar

from mcdreforged.api.all import *

from region_file_updater_multi.region_upstream_manager import Region
from region_file_updater_multi.mcdr_globals import CommandCallback
from region_file_updater_multi.utils.misc_tools import get_player_from_src, RFUMInstance
from region_file_updater_multi.utils.serializer import RFUMSerializable

if TYPE_CHECKING:
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti


T = TypeVar("T")


@dataclass
class GroupPermissionItem:
    is_admin: bool
    is_update_allowed: bool

    def get_update_allowed_flag(self):
        config = RFUMInstance.get_rfum().config
        return (
            self.is_update_allowed
            or not config.region_protection.enable_group_update_permission_check
        )


class GroupPermission(GroupPermissionItem, Enum):
    admin = True, True
    user = False, True
    denied = False, False


class GroupFileData(RFUMSerializable):
    name: str = ""
    regions: List[Region] = []
    default_permission: GroupPermission = GroupPermission.user
    player_permission: Dict[str, GroupPermission] = {}


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
        self.__cached_data: Optional["GroupFileData"] = None

    @property
    def name(self):
        return self.__data.name

    @property
    def regions(self):
        return self.__data.regions

    @property
    def is_present(self):
        return self.__manager.is_present(self)

    @property
    def default_permission(self):
        return self.__data.default_permission

    @property
    def permission_mapping(self):
        return self.__data.player_permission

    def get_required_perm_players(self, target_permission: GroupPermission):
        for player, perm in self.__data.player_permission.items():
            if perm is target_permission:
                yield player

    def add_region(self, region: "Region"):
        with self.__lock:
            if self.is_listed(region):
                return False
            self.regions.append(region)
            if not self.requires_save:
                RFUMInstance.get_rfum().verbose(f"{region} added and not saved")
                return True
            RFUMInstance.get_rfum().verbose(f"{region} added")
            return self.save()

    def remove_region(self, region: "Region"):
        with self.__lock:
            if not self.is_listed(region):
                return False
            self.regions.remove(region)
            if not self.requires_save:
                return True
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

    def get_player_permission(
        self, player: str, default: Optional[T] = None
    ) -> Union[GroupPermission, T]:
        with self.__lock:
            if default is None:
                default = self.default_permission
            return self.__data.player_permission.get(player, default)

    def get_source_permission(self, source: CommandSource):
        with self.__lock:
            player = get_player_from_src(source)
            if player is None:
                return GroupPermission.admin
            return self.get_player_permission(player)

    def is_src_permitted(self, source: CommandSource):
        with self.__lock:
            return self.get_source_permission(source).is_update_allowed

    def is_src_admin(self, source: CommandSource):
        with self.__lock:
            return self.get_source_permission(source).is_admin

    def set_permission(self, player: str, permission: GroupPermission):
        with self.__lock:
            self.__data.player_permission[player] = permission
            if not self.requires_save:
                return True
            return self.save()

    def remove_permission(self, player: str):
        with self.__lock:
            if player not in self.__data.player_permission.keys():
                return False
            del self.__data.player_permission[player]
            if not self.requires_save:
                return True
            return self.save()

    def set_default_permission(self, permission: GroupPermission):
        with self.__lock:
            self.__data.default_permission = permission
            if not self.requires_save:
                return True
            return self.save()

    @contextlib.contextmanager
    def keep_modify_context(self):
        with self.__lock:
            self.__cached_data = self.__data
            self.__data = deepcopy(self.__data)
            try:
                yield
            finally:
                self.__data = self.__cached_data
                self.__cached_data = None

    @property
    def requires_save(self):
        return self.__cached_data is None


class GroupManager:
    def __init__(self, path: str, rfum: "RegionFileUpdaterMulti"):
        self.__lock = threading.RLock()
        self.__path = path
        self.__rfum = rfum
        self.__groups: Dict[str, Group] = {}
        self.load()

    @property
    def groups(self):
        return self.__groups

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
            data_list = map(lambda group: group.get_data(self), self.__groups.values())
            if os.path.isdir(self.__path):
                os.removedirs(self.__path)
            try:
                with open(self.__path, "w", encoding="utf8") as f:
                    json.dump(
                        serialize(list(data_list)), f, ensure_ascii=False, indent=4
                    )
            except (KeyError, ValueError):
                self.__rfum.logger.exception("Saving group file failed")
                return False
            else:
                self.__rfum.verbose("Saved group file")
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
                self.__rfum.verbose(f"{region} included in {group.name}")
                yield group

    def get_update_denied_groups(self, source: CommandSource, region: Region):
        return filter(
            lambda group: not group.is_src_permitted(source),
            self.get_group_by_region(region),
        )

    def is_region_permitted(self, source: CommandSource, region: Region):
        return len(list(self.get_update_denied_groups(source, region))) == 0

    def is_region_included(self, region: Region):
        return len(list(self.get_group_by_region(region))) > 0
