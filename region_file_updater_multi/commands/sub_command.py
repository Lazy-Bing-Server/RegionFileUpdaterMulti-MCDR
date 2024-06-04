from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Callable,
    Any,
    Optional,
    List,
    Type,
    TypeVar,
    Iterable,
    Union,
    Tuple,
)
from queue import Queue
from threading import RLock
from types import MethodType

import inspect

from mcdreforged.api.all import *
from typing_extensions import Self, TypeAlias

from region_file_updater_multi.region_upstream_manager import Region
from region_file_updater_multi.mcdr_globals import *
from region_file_updater_multi.commands.tree_constants import *
from region_file_updater_multi.commands.node_factory import DurationNode
from region_file_updater_multi.components.misc import get_rfum_comp_prefix


if TYPE_CHECKING:
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti


AnyNode = TypeVar("AnyNode", bound=AbstractNode)


class AbstractSubCommand(ABC):
    def __init__(self, rfum: "RegionFileUpdaterMulti"):
        self.__rfum = rfum
        self.__queue: Queue[Callable] = Queue()
        self.__running = True
        self.__tick_lock = RLock()

    @property
    def rfum(self):
        return self.__rfum

    def verbose(self, msg: MessageText):
        return self.__rfum.verbose(msg)  # type: ignore[arg-type]

    @property
    def logger(self):
        return self.__rfum.logger

    @property
    def server(self):
        return self.__rfum.server

    @property
    def config(self):
        return self.__rfum.config

    @property
    def command_manager(self):
        return self.__rfum.command_manager

    @property
    def prefixes(self):
        return self.command_manager.prefixes

    def rtr(
        self,
        translation_key: str,
        *args,
        _lb_rtr_prefix: Optional[str] = None,
        **kwargs,
    ):
        return self.command_manager.rtr(
            translation_key, *args, _lb_rtr_prefix=_lb_rtr_prefix, **kwargs
        )

    def ctr(
        self,
        translation_key: str,
        *args,
        _lb_rtr_prefix: Optional[str] = None,
        **kwargs,
    ):
        _lb_rtr_prefix = _lb_rtr_prefix or self.tr_key_prefix
        return self.command_manager.rtr(
            translation_key, *args, _lb_rtr_prefix=_lb_rtr_prefix, **kwargs
        )

    def htr(
        self,
        translation_key: str,
        *args,
        prefixes: Optional[List[str]] = None,
        suggest_prefix: Optional[str] = None,
        _lb_rtr_prefix: Optional[str] = None,
        **kwargs,
    ) -> RTextMCDRTranslation:
        _lb_rtr_prefix = _lb_rtr_prefix or TRANSLATION_KEY_PREFIX + "command."
        return self.__rfum.htr(
            translation_key,
            *args,
            prefixes=prefixes,
            suggest_prefix=suggest_prefix,
            _lb_rtr_prefix=_lb_rtr_prefix,
            **kwargs,
        )

    def get_threaded_node(self, target_node_cls: TypeAlias) -> Type[AnyNode]:
        cmd = self

        class NewNodeClass(target_node_cls):
            def runs(self, func: CommandCallback[Any]) -> "Self":
                return super().runs(cmd.get_func_work(func))

        NewNodeClass.__name__ = f"_{target_node_cls.__name__}"
        return NewNodeClass

    def add_work(self, func: Callable, *args, **kwargs) -> Any:
        if not callable(func):
            raise TypeError(f"{func} is not callable")
        return self.command_manager.add_work(
            func, *args, _payload_add_is_complex=self.is_complex, **kwargs
        )

    def get_func_work(self, callback: CommandCallback[Any]) -> CommandCallback[Any]:
        # From MCDReforged (https://github.com/Fallen-Breath/MCDReforged)
        # mcdreforged.command.builder.nodes.basic.AbstractNode.__smart_callback()
        # Commit SHA: 850e28fce8ad624fbdd9501f5a5faae3d3ef57f3 / Licensed under LGPL-v3.0
        def invoke(source: CommandSource, context: CommandContext):
            args = [source, context]
            sig = inspect.signature(callback)
            spec_args = inspect.getfullargspec(callback).args
            spec_args_len = len(spec_args)
            if isinstance(callback, MethodType):  # class method, remove the 1st param
                spec_args_len -= 1
            try:
                sig.bind(*args[:spec_args_len])  # test if using full arg length is ok
            except TypeError:
                raise

            # make sure all passed CommandContext are copies
            args = list(args)
            for i, arg in enumerate(args):
                if isinstance(arg, CommandContext):
                    args[i] = arg.copy()
            return self.add_work(callback, *args[:spec_args_len])

        return invoke

    @staticmethod
    def get_ctx_flag(context: CommandContext, flags_name: str):
        return context.get(flags_name, 0) > 0

    @property
    @abstractmethod
    def is_debug_command(self) -> bool: ...

    @abstractmethod
    def add_children_for(self, root_node: AbstractNode) -> Any: ...

    @property
    @abstractmethod
    def tr_key_prefix(self) -> str: ...

    @property
    @abstractmethod
    def is_complex(self) -> bool: ...

    @property
    def literal(self) -> Type[Literal]:
        return self.get_threaded_node(Literal)

    @property
    def quotable_text(self) -> Type[QuotableText]:
        return self.get_threaded_node(QuotableText)

    @property
    def greedy_text(self) -> Type[GreedyText]:
        return self.get_threaded_node(GreedyText)

    @property
    def integer(self) -> Type[Integer]:
        return self.get_threaded_node(Integer)

    @property
    def duration(self) -> Type[DurationNode]:
        return self.get_threaded_node(DurationNode)

    @property
    def enumeration(self) -> Type[Enumeration]:
        return self.get_threaded_node(Enumeration)

    @property
    def counting_literal(self) -> Type[CountingLiteral]:
        return self.get_threaded_node(CountingLiteral)

    def register_event_listeners(self) -> Any:
        pass

    def permed_literal(
        self,
        literal_name: Union[str, Literal, NodeDefinition[Literal]],
        node_type: Optional[Type[Literal]] = None,
    ) -> Union[Literal]:
        return self.command_manager.permed_literal(
            literal_name, node_type=node_type or self.literal
        )

    def perm_denied(self, source: CommandSource):
        return source.reply(
            get_rfum_comp_prefix(self.rfum.command_manager.perm_denied_text_getter())
        )

    def list_command_factory(
        self, node_base: Union[str, Iterable[str], Literal]
    ) -> Literal:
        if not isinstance(node_base, Literal):
            node = self.literal(node_base)
        else:
            node = node_base
        node.then(self.literal("--page").then(Integer(PAGE_INDEX).redirects(node)))
        node.then(
            self.literal("--per-page").then(Integer(ITEM_PER_PAGE).redirects(node))
        )
        return node

    def get_list_args(self, context: CommandContext) -> Tuple[int, int]:
        return context.get(PAGE_INDEX, 1), context.get(
            ITEM_PER_PAGE, self.config.default_item_per_page
        )

    @staticmethod
    def get_list_command_args_format() -> str:
        return "--page {page} --per-page {item_per_page}"

    def set_builder_coordinate_args(
        self,
        b: SimpleCommandBuilder,
        x_f: Optional[Union[Type[ArgumentNode], Callable]] = None,
        z_f: Optional[Union[Type[ArgumentNode], Callable]] = None,
        d_f: Optional[Union[Type[ArgumentNode], Callable]] = None,
    ) -> Any:
        b.arg(X, x_f or self.integer)
        b.arg(Z, z_f or self.integer)
        b.arg(DIM, d_f or self.quotable_text).requires(
            lambda src, ctx: ctx[DIM]
            in self.__rfum.config.paths.dimension_mca_files.keys(),
            lambda src, ctx: self.rtr("add_del.error.invalid_dimension", ctx[DIM]),
        ).suggests(lambda: self.__rfum.config.paths.dimension_mca_files.keys())

    def is_session_running(self, source: CommandSource, silent=False) -> bool:
        if self.rfum.current_session.is_session_running and not silent:
            source.reply(
                get_rfum_comp_prefix(self.rtr("error_message.session_running"))
            )
        return self.rfum.current_session.is_session_running

    @staticmethod
    def get_ctx_coordinates(context: CommandContext) -> Tuple[int, int, str]:
        return context[X], context[Z], str(context[DIM])

    def get_region_from_player(self, player: str):
        api = self.server.get_plugin_instance(MINECRAFT_DATA_API)
        coord = api.get_player_coordinate(
            player, timeout=self.config.get_mc_data_api_timeout()
        )
        dim = api.get_player_dimension(
            player, timeout=self.config.get_mc_data_api_timeout()
        )
        return Region.from_player_coordinates(coord.x, coord.z, str(dim))
