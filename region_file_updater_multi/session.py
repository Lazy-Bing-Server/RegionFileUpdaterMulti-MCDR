import threading
from typing import TYPE_CHECKING, Dict, overload, Optional

from mcdreforged.api.types import PlayerCommandSource, CommandSource

from region_file_updater_multi.region import Region
from sched import scheduler

from minecraft_data_api import get_player_coordinate, get_player_dimension

if TYPE_CHECKING:
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti


class CurrentSession:
    def __init__(self, rfum: "RegionFileUpdaterMulti"):
        self.__lock = threading.RLock()
        self.__regions: Dict[Region, str] = {}
        self.__rfum = rfum

    @staticmethod
    def get_region_from_player(player: str):
        coord = get_player_coordinate(player)
        dim = get_player_dimension(player)
        return Region.from_player_coordinates(coord.x, coord.z, dim)

    def add_region(self, region: Region, player: Optional[str]):
        if region in self.__regions.keys():
            raise ValueError(f'{repr(region)} already exists')
        self.__regions[region] = player

    def remove_region(self, region: Region):
        if region not in self.__regions.keys():
            raise ValueError(f'{repr(region)} not found in current session')
        del self.__regions[region]
