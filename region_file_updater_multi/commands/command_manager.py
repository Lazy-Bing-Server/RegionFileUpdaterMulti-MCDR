import threading

from queue import Queue, Empty
from dataclasses import dataclass

from mcdreforged.api.all import *
from typing import (
    TYPE_CHECKING,
    Union,
    Callable,
    Optional,
    Any,
    List,
    Type,
)

from region_file_updater_multi.commands.tree_constants import *
from region_file_updater_multi.commands.sub_command import AbstractSubCommand
from region_file_updater_multi.mcdr_globals import *
from region_file_updater_multi.utils.misc_tools import named_thread
from region_file_updater_multi.components.misc import get_rfum_comp_prefix

if TYPE_CHECKING:
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti


@dataclass
class CommandWork:
    command_inst: "AbstractSubCommand"
    callback: CommandCallback[Any]


class CommandManager:
    def __init__(self, rfum: "RegionFileUpdaterMulti"):
        self.__rfum = rfum
        self.__queue: Queue[CommandWork] = Queue()
        self.__tick_lock = threading.RLock()
        self.__running = True
        self.__thread: Optional[FunctionThread] = None
        self.__registered_commands: List[AbstractSubCommand] = []
        self.__start()

    def __start(self):
        @named_thread("CommandManager")
        def main_loop():
            while True:
                self.__tick()
                if not self.__running:
                    self.__rfum.verbose("CommandManager thread terminated")
                    break
            self.__thread = None

        if self.is_normal:
            raise RuntimeError("Command executor already running")
        self.__thread: FunctionThread = main_loop()  # type: ignore[annotation-unchecked]

    @property
    def server(self):
        return self.__rfum.server

    @property
    def config(self):
        return self.__rfum.config

    @property
    def is_normal(self):
        return self.__thread is not None

    @property
    def prefixes(self):
        prefixes = self.__rfum.config.command.command_prefix
        if isinstance(prefixes, list):
            return prefixes
        return [prefixes]

    def add_work(
        self, command_inst: AbstractSubCommand, func: Callable, *args, **kwargs
    ):
        if not self.is_normal:
            raise RuntimeError("Can't add work to a stopped command executor")
        self.__queue.put(CommandWork(command_inst, lambda: func(*args, **kwargs)))

    def __shutdown(self, *args, **kwargs):
        self.__running = False
        with self.__tick_lock:
            self.__queue = Queue()

    def __tick(self):
        with self.__tick_lock:
            try:
                work = self.__queue.get(block=True, timeout=0.01)
            except Empty:
                pass
            else:
                self.__rfum.verbose("CommandManager executing work...")
                work.command_inst.execute(work.callback)

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
        command.register_event_listener()

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
        self.__rfum.server.register_event_listener(
            MCDRPluginEvents.PLUGIN_UNLOADED, self.__shutdown
        )

    def permission_checker(self, source: CommandSource, context: CommandContext):
        split_cmd = context.command.split(" ")
        return source.has_permission(
            self.__rfum.config.command.permission.get(split_cmd[1], 0)
        )

    def perm_denied_text_getter(self):
        return self.rtr("error_message.permission_denied")

    def permed_literal(
        self,
        literal_name: Union[str, Literal, NodeDefinition[Literal]],
        node_type: Optional[Type[Literal]] = None,
    ):
        literal_type = node_type or Literal
        node: Union[Literal, NodeDefinition]
        if isinstance(literal_name, str):
            node = literal_type(literal_name)
        else:
            node = literal_name
        return node.requires(self.permission_checker, self.perm_denied_text_getter)
