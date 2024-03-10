from mcdreforged.api.all import *

from region_file_updater_multi.rfum import RegionFileUpdaterMulti


__main = RegionFileUpdaterMulti()


def on_load(server: PluginServerInterface, prev_module):
    if not __main.config.enabled:
        __main.logger.warning('RegionFileUpdaterMulti is disabled by config')
        __main.server.unload_plugin(__main.server.get_self_metadata().id)
        return
    __main.on_load(server, prev_module)
