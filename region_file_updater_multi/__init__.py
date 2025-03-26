from mcdreforged.api.all import *
from typing import Any

from region_file_updater_multi.rfum import RegionFileUpdaterMulti


__rfum = RegionFileUpdaterMulti()


def on_load(server: PluginServerInterface, prev_module) -> Any:
    if __rfum.config.enabled:
        __rfum.on_load(server, prev_module)
    else:
        __rfum.logger.warning("RegionFileUpdaterMulti is disabled by config")
        server.schedule_task(lambda: server.unload_plugin(server.get_self_metadata().id))
