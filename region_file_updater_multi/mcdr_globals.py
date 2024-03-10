import os
from typing import Union, TypeVar, Callable
from mcdreforged.api.all import *


__all__ = [
    'CONFIG_FILE',
    'LOG_FILE',
    'HISTORY_FILE',
    'GROUP_FILE',
    'RECYCLE_BIN_FOLDER',
    'RECYCLED_FILE_META',
    'RECYCLED_FILE_NAME',
    'CLI_STDOUT_LOG_FILE',
    'CUSTOM_TRANSLATION_FOLDER',
    'SELF_PLUGIN_CFG_TEMPLATE_PATH',
    'DEBUG_TEMP_FOLDER',

    'SELF_PLUGIN_ABBR',
    'SELF_PLUGIN_ID',
    'SELF_PLUGIN_NAME',
    'SELF_PLUGIN_NAME_SHORT',
    'TRANSLATION_KEY_PREFIX',
    'SELF_PLUGIN_PACKAGE_PATH',

    'PB_LOGGER_NAME',
    'PRIME_BACKUP_ID',
    'MCDR_CFG_DECODING_KEY',
    'LATEST',

    'MessageText',
    'CommandCallback',
    'PathLike'
]


# File structure
# - config/region_file_updater_multi
#     - lang
#     - .recycle_bin
#     config.yml
#     range.json
#     history.json
#     rfu_multi.log

CONFIG_FILE = 'config.yml'
LOG_FILE = 'rfu_multi.log'
HISTORY_FILE = 'history.json'
GROUP_FILE = 'group.json'
RECYCLE_BIN_FOLDER = '.recycle_bin'
RECYCLED_FILE_META = '.rfu_multi.recycled.json'
RECYCLED_FILE_NAME = '.recycled'
CLI_STDOUT_LOG_FILE = 'cli.log'
PB_LOGGER_NAME = 'PB'
CUSTOM_TRANSLATION_FOLDER = 'lang'
DEBUG_TEMP_FOLDER = 'debug'

# Plugin
SELF_PLUGIN_ABBR = 'RFUM'
SELF_PLUGIN_ID = 'region_file_updater_multi'
SELF_PLUGIN_NAME = 'Region File Updater Multi'
SELF_PLUGIN_NAME_SHORT = 'RFU_Multi'
TRANSLATION_KEY_PREFIX = SELF_PLUGIN_ID + '.'

SELF_PLUGIN_PACKAGE_PATH = os.path.dirname(os.path.dirname(__file__))
SELF_PLUGIN_CFG_TEMPLATE_PATH = os.path.join("resources", "default_cfg.yml")

# Prime Backup CLI
PRIME_BACKUP_ID = 'prime_backup'
MCDR_CFG_DECODING_KEY = 'decoding'  # MCDReforged config decoding method
LATEST = 'latest'


# Global generics
MessageText = Union[str, RTextBase]
__T = TypeVar('__T')
CommandCallback = Union[
    Callable[[], __T],
    Callable[[CommandSource], __T],
    Callable[[CommandSource, CommandContext], __T]
]
PathLike = Union[str, os.PathLike]
