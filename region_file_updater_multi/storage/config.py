import sys
from typing import Dict, Union, List, Any, Optional, TYPE_CHECKING

from region_file_updater_multi.mcdr_globals import PrimeBackupLogParsingArguments
from region_file_updater_multi.utils.serializer import (
    BlossomSerializable,
    ConfigurationBase,
)
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
        command_prefix: Union[List[str], str] = ["!!rfum", "!!region"]

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
                UPSTREAM: 3,
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
        confirm_time_wait: Duration = Duration("1min")
        update_delay: Duration = Duration("10s")
        prime_backup_file_not_found_log_format: List[str] = [
            "File '{file_name}' in backup #{backup_id:d} does not exist"
        ]
        remove_file_while_not_found: bool = False

    update_operation: UpdateOperation = UpdateOperation.get_default()

    class Paths(BlossomSerializable):
        pb_plugin_package_path: Optional[str] = None
        destination_world_directory: str = "./server/world"
        current_upstream: str = "survival_pb"

        class Upstream(BlossomSerializable):
            type: str = "world"
            path: str = "../survival/qb_multi/slot1"
            world_name: str = "world"

            def validate_attribute(self, attr_name: str, attr_value: Any, **kwargs):
                if attr_name == "type" and attr_value not in ["prime_backup", "world"]:
                    raise ValueError("Invalid upstream type provided")

        upstreams: Optional[Dict[str, Upstream]] = {
            "survival_pb": Upstream.deserialize(
                dict(type="prime_backup", path="../survival/pb_files/prime_backup.db")
            ),
            "survival_qb": Upstream.get_default(),
        }
        dimension_mca_files: Dict[str, Union[str, List[str]]] = {
            "-1": [
                "DIM{dim}/region/r.{x}.{z}.mca",
                "DIM{dim}/poi/r.{x}.{z}.mca",
                "DIM{dim}/entities/r.{x}.{z}.mca"
            ],
            "0": [
                "region/r.{x}.{z}.mca",
                "poi/r.{x}.{z}.mca",
                "entities/r.{x}.{z}.mca"
            ],
            "1": [
                "DIM{dim}/region/r.{x}.{z}.mca",
                "DIM{dim}/poi/r.{x}.{z}.mca",
                "DIM{dim}/entities/r.{x}.{z}.mca"
            ],
        }

    paths: Paths = Paths.get_default()

    class RegionProtection(BlossomSerializable):
        enable_group_update_permission_check: bool = True
        check_add_groups: bool = True
        check_del_operations: bool = False
        permission_modify_repeat_wait_time: Duration = Duration("1m")
        suppress_warning: bool = False

    region_protection: RegionProtection = RegionProtection.get_default()

    class Debug(BlossomSerializable):
        verbosity: bool
        enable_debug_commands: bool
        popen_decoding: str
        python_executable: str
        popen_terminate_timeout: int
        prime_backup_log_format: List[str]
        thread_pool_executor_max_workers: int
        attach_plugin_log_handler: bool
        lost_permission_requires_confirm: bool
        minecraft_data_api_timeout: float
        enable_custom_language_filter: bool

    experimental: Optional[Debug] = None

    def validate_attribute(self, attr_name: str, attr_value: Any, **kwargs):
        if attr_name == "command_prefix":
            if isinstance(attr_value, str):
                attr_value = [attr_value]
                for p in attr_value:
                    if " " in p:
                        raise ValueError("Illegal command prefix with space found")

    def get_debug_options(self):
        return self.experimental or self.Debug.get_default()

    def get_mc_data_api_timeout(self):
        return self.get_debug_options().get("minecraft_data_api_timeout", 10)

    def get_verbosity(self):
        return self.get_debug_options().get("verbosity", False)

    def get_enable_debug_commands(self):
        return self.get_debug_options().get("enable_debug_commands", False)

    def get_python_executable(self):
        return self.get_debug_options().get("python_executable", sys.executable)

    def get_popen_decoding(self):
        return self.get_debug_options().get("popen_decoding")

    def get_popen_terminate_timeout(self):
        return self.get_debug_options().get("popen_terminate_timeout", 5)

    def get_pb_log_format(self):
        args = PrimeBackupLogParsingArguments
        return self.get_debug_options().get(
            "prime_backup_log_format",
            [
                f"[{args.YEAR}-{args.MONTH}-{args.DAY} {args.HOUR}:{args.MINUTE}:{args.SECOND},{args.SEC_DECIMAL} {args.LEVEL}] {args.MSG}"
            ],
        )

    def get_thread_pool_executor_max_workers(self):
        return self.get_debug_options().get("thread_pool_executor_max_workers", 10)

    def get_attach_log_handler(self):
        return self.get_debug_options().get("attach_plugin_log_handler", True)

    def get_lost_permission_requires_confirm(self):
        return self.get_debug_options().get("lost_permission_requires_confirm", True)

    def get_enable_custom_language_filter(self):
        return self.get_debug_options().get("enable_custom_language_filter", True)
