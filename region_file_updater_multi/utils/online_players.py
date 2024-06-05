from typing import TYPE_CHECKING, List
from threading import RLock

from mcdreforged.api.all import *

from region_file_updater_multi.mcdr_globals import MINECRAFT_DATA_API
from region_file_updater_multi.utils.misc_tools import named_thread

if TYPE_CHECKING:
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti


class OnlinePlayers:
    def __init__(self, rfum: "RegionFileUpdaterMulti"):
        self.__lock = RLock()
        self.__players: List[str] = []
        self.__rfum = rfum
        self.__limit = 0
        self.__enabled = False

    def get_player_list(self, refresh: bool = False):
        with self.__lock:
            if refresh:
                self.__refresh_online_players()
            return self.__players.copy()

    def get_player_limit(self, refresh: bool = False):
        with self.__lock:
            if refresh or self.__limit is None:
                self.__refresh_online_players()
            return self.__limit

    @named_thread
    def __add_player(self, player: str):
        with self.__lock:
            if self.__enabled and player not in self.__players:
                self.__players.append(player)

    @named_thread
    def __remove_player(self, player: str):
        with self.__lock:
            if self.__enabled and player in self.__players:
                self.__players.remove(player)

    @named_thread
    def __refresh_online_players(self):
        with self.__lock:
            self.__rfum.verbose("Refreshing online players")
            if not self.__rfum.server.is_server_startup():
                return
            api = self.__rfum.server.get_plugin_instance(MINECRAFT_DATA_API)
            if api is None:
                self.__rfum.logger.warning("Minecraft Data API is not installed, some function may not work properly")
                return
            timeout = self.__rfum.config.get_mc_data_api_timeout()
            self.__rfum.verbose(f"Minecraft Data API timeout = {timeout}")
            player_tuple = api.get_server_player_list(timeout=timeout)

            if player_tuple is not None:
                count, self.__limit, self.__players = player_tuple
                self.__rfum.verbose(
                    "Player list refreshed: "
                    + ", ".join(self.__players)
                    + f" (max {self.__limit})"
                )
                if count != len(self.__players):
                    self.__rfum.logger.warning(
                        "Incorrect player count found while refreshing player list"
                    )
            self.__enabled = True

    @named_thread
    def __enable_player_join(self):
        with self.__lock:
            self.__enabled = True
            self.__rfum.verbose("Player list counting enabled")

    @named_thread
    def __clear_online_players(self):
        with self.__lock:
            self.__limit, self.__players = None, []
            self.__enabled = False
            self.__rfum.verbose(
                "Cleared online player cache, player list counting disabled"
            )

    def register_event_listeners(self):
        server = self.__rfum.server
        server.register_event_listener(
            MCDRPluginEvents.PLUGIN_LOADED,
            lambda *args, **kwargs: self.__refresh_online_players(),
        )
        server.register_event_listener(
            MCDRPluginEvents.SERVER_START,
            lambda *args, **kwargs: self.__enable_player_join(),
        )
        server.register_event_listener(
            MCDRPluginEvents.PLAYER_JOINED,
            lambda _, player, __: self.__add_player(player),
        )
        server.register_event_listener(
            MCDRPluginEvents.PLAYER_LEFT, lambda _, player: self.__remove_player(player)
        )
        server.register_event_listener(
            MCDRPluginEvents.SERVER_STOP,
            lambda *args, **kwargs: self.__clear_online_players(),
        )
