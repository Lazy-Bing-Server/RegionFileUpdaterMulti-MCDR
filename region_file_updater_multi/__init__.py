from mcdreforged.api.all import *
from typing import Any

from region_file_updater_multi.rfum import RegionFileUpdaterMulti


__rfum = RegionFileUpdaterMulti()


def on_load(server: PluginServerInterface, prev_module) -> Any:
    if not __rfum.config.enabled:
        __rfum.logger.warning("RegionFileUpdaterMulti is disabled by config")
        return __rfum.server.unload_plugin(__rfum.server.get_self_metadata().id)
    __rfum.on_load(server, prev_module)
