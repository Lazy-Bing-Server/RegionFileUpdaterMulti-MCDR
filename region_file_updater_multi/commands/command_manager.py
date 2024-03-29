from typing import (
    TYPE_CHECKING,
    Union,
    Callable,
    Optional,
    List,
    Type,
)

from mcdreforged.api.all import *

from region_file_updater_multi.commands.sub_command import AbstractSubCommand
from region_file_updater_multi.commands.tree_constants import *
from region_file_updater_multi.components.misc import get_rfum_comp_prefix
from region_file_updater_multi.mcdr_globals import *

if TYPE_CHECKING:
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti


class CommandManager:
    def __init__(self, rfum: "RegionFileUpdaterMulti"):
        self.__rfum = rfum
        self.__registered_commands: List[AbstractSubCommand] = []

    @property
    def server(self):
        return self.__rfum.server

    @property
    def config(self):
        return self.__rfum.config

    @property
    def prefixes(self):
        prefixes = self.__rfum.config.command.command_prefix
        if isinstance(prefixes, list):
            return prefixes
        return [prefixes]

    def add_work(
        self, func: Callable, *args, _payload_add_is_complex: bool = False, **kwargs
    ):
        self.__rfum.payload_executor.add_work(
            func, *args, _payload_add_is_complex=_payload_add_is_complex, **kwargs
        )

    def rtr(
        self,
        translation_key: str,
        *args,
        _lb_rtr_prefix: Optional[str] = None,
        **kwargs,
    ):
        _lb_rtr_prefix = _lb_rtr_prefix or TRANSLATION_KEY_PREFIX + "command."
        return self.__rfum.rtr(
            translation_key, *args, _lb_rtr_prefix=_lb_rtr_prefix, **kwargs
        )

    def plugin_overview(self, source: CommandSource, context: CommandContext):
        meta = self.__rfum.server.get_self_metadata()
        version = meta.version
        current_prefix = context.command.split(" ")[0]
        version_str = (
            ".".join([str(n) for n in version.component]) + "-" + str(version.pre)
        )
        source.reply(
            self.__rfum.htr(
                "command.help.overview",
                plugin_name=meta.name,
                version=version_str,
                pre=current_prefix,
                prefixes=self.prefixes,
                help=HELP,
                upstream=UPSTREAM,
                add=ADD,
                del_=DEL,
                del_all=DEL_ALL,
                list=LIST,
                history=HISTORY,
                group=GROUP,
                update=UPDATE,
                reload=RELOAD,
            )
        )

    def reload_self(self, source: CommandSource):
        self.server.reload_plugin(self.server.get_self_metadata().id)
        source.reply(get_rfum_comp_prefix(self.rtr(f"{RELOAD}.reloaded")))

    def add_command(self, command: "AbstractSubCommand"):
        self.__registered_commands.append(command)
        command.register_event_listeners()

    def get_command(
        self, rfum: "RegionFileUpdaterMulti", command: Type[AbstractSubCommand]
    ):
        if rfum is not self.__rfum:
            raise RuntimeError("Not allowed operation")
        for item in self.__registered_commands:
            if isinstance(item, command):
                return item

    def register(self):
        root_node = (
            Literal(self.prefixes)
            .runs(self.plugin_overview)
            .then(self.permed_literal(RELOAD).runs(self.reload_self))
        )
        sub_commands: List[AbstractSubCommand] = self.__registered_commands.copy()  # type: ignore[annotation-unchecked]
        self.__rfum.verbose(f"{len(sub_commands)} commands was added")
        for item in sub_commands:
            if not item.is_debug_command or self.config.get_enable_debug_commands():
                item.add_children_for(root_node)
            else:
                self.__rfum.verbose(f"{item.__class__.__name__} ignored")
        root_node.print_tree(self.__rfum.verbose)
        self.__rfum.server.register_command(root_node)

    def permission_checker(self, source: CommandSource, context: CommandContext):
        split_cmd = context.command.split(" ")
        return source.has_permission(
            self.__rfum.config.command.permission.get(split_cmd[1], 0)
        )

    def perm_denied_text_getter(self):
        return self.rtr("error_message.permission_denied").set_color(RColor.red)

    def permed_literal(
        self,
        literal_name: Union[str, Literal],
        node_type: Optional[Type[Literal]] = None,
    ):
        literal_type = node_type or Literal
        if isinstance(literal_name, str):
            node = literal_type(literal_name)
        else:
            node = literal_name
        return node.requires(
            self.permission_checker,
            lambda: get_rfum_comp_prefix(self.perm_denied_text_getter()),
        )
