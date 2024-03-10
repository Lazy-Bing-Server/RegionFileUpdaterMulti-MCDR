import sys
from typing import Dict, Union, List, Any, Optional, TYPE_CHECKING, get_type_hints

from region_file_updater_multi.mcdr_globals import PRIME_BACKUP_ID
from region_file_updater_multi.utils.serializer import BlossomSerializable, ConfigurationBase
from region_file_updater_multi.commands.tree_constants import *
from region_file_updater_multi.utils.units import Duration

if TYPE_CHECKING:
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti


class Config(ConfigurationBase):
    __rfum = None

    @classmethod
    def set_rfum(cls, rfum: "RegionFileUpdaterMulti"):
        cls.__rfum = rfum

    enabled: bool = False
    load_custom_translation: bool = True
    default_item_per_page: int = 10

    class Command(BlossomSerializable):
        command_prefix: Union[List[str], str] = '!!rfum'

        class Permission(BlossomSerializable):
            __default = {
                RELOAD: 2,
                ADD: 0,
                DEL: 0,
                DEL_ALL: 1,
                LIST: 0,
                HISTORY: 1,
                UPDATE: 2,
                GROUP: 2,
                UPSTREAM: 3
            }
            __dict__ = __default
            __annotations__ = {}
            for key in __default:
                __annotations__[key] = int
            __annotations__[DEBUG] = int

            @classmethod
            def default_dict(cls):
                return cls.__default

        permission: Permission = Permission.get_default()

    command: Command = Command.get_default()

    class UpdateOperation(BlossomSerializable):
        update_requires_confirm: bool = True
        confirm_time_wait: Duration = Duration('1min')
        update_delay_in_seconds: Duration = Duration('10s')

    update_operation: UpdateOperation = UpdateOperation.get_default()

    class Paths(BlossomSerializable):
        pb_plugin_package_path: Optional[str] = None
        destination_world_directory: str = './server/world'
        current_upstream: str = 'survival_pb'

        class Upstream(BlossomSerializable):
            type: str = 'world'
            path: str = "../survival/qb_multi/slot1"
            world_name: str = 'world'

            def validate_attribute(self, attr_name: str, attr_value: Any, **kwargs):
                if attr_name == 'type' and attr_value not in ['prime_backup', 'world']:
                    raise ValueError("Invalid upstream value provided")

        upstreams: Optional[Dict[str, Upstream]] = {
            'survival_pb': Upstream.deserialize(dict(type='prime_backup', path="../survival/pb_files/prime_backup.db")),
            'survival_qb': Upstream.get_default(),
        }
        dimension_region_folder: Dict[str, Union[str, List[str]]] = {
            '-1': ['DIM-1/region', 'DIM-1/poi'],
            '0': ['region', 'poi'],
            '1': ['DIM1/region', 'DIM1/poi']
        }

    paths: Paths = Paths.get_default()

    verbosity: bool
    enable_debug_commands: bool

    popen_decoding: str
    python_executable: str
    popen_terminate_timeout: int

    def validate_attribute(self, attr_name: str, attr_value: Any, **kwargs):
        if attr_name == 'command_prefix':
            if isinstance(attr_value, str):
                attr_value = [attr_value]
                for p in attr_value:
                    if ' ' in p:
                        raise ValueError("Illegal command prefix with space found")

    def get_verbosity(self):
        return self.get('verbosity', False)

    def get_enable_debug_commands(self):
        return self.get('enable_debug_commands', False)

    def get_python_executable(self):
        return self.get('python_executable', sys.executable)

    def get_popen_decoding(self):
        return self.get('popen_decoding')

    def get_popen_terminate_timeout(self):
        return self.get('popen_terminate_timeout', 5)
