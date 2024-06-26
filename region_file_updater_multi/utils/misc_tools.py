import sys
import inspect
import functools
import threading

from mcdreforged.api.decorator import FunctionThread
from mcdreforged.api.types import CommandSource, PlayerCommandSource
from typing import Optional, Callable, Union, TYPE_CHECKING, Any, Type, TypeVar
from concurrent.futures.thread import ThreadPoolExecutor as ConcurrentTPE
from apscheduler.executors.pool import ThreadPoolExecutor as APSchedulerTPE
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import BaseScheduler

from region_file_updater_multi.mcdr_globals import (
    SELF_PLUGIN_NAME_SHORT,
)

if TYPE_CHECKING:
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti


class RFUMInstance:
    __rfum: Optional["RegionFileUpdaterMulti"] = None

    @classmethod
    def set_rfum(cls, rfum: "RegionFileUpdaterMulti"):
        cls.__rfum = rfum

    @classmethod
    def get_rfum(cls):
        return cls.__rfum


def capitalize(string: str) -> str:
    char_list = list(string)
    if len(char_list) > 0:
        char_list[0] = char_list[0].upper()
    return "".join(char_list)


def to_camel_case(string: str, divider: str = " ", upper: bool = True) -> str:
    word_list = [capitalize(item) for item in string.split(divider)]
    if not upper:
        first_word_char_list = list(word_list[0])
        first_word_char_list[0] = first_word_char_list[0].lower()
        word_list[0] = "".join(first_word_char_list)
    return "".join(word_list)


def get_thread_prefix() -> str:
    return to_camel_case(SELF_PLUGIN_NAME_SHORT, divider="_") + "@"


def named_thread(arg: Optional[Union[str, Callable]] = None) -> Callable:
    rfum = RFUMInstance.get_rfum()

    def wrapper(func):
        @functools.wraps(func)
        def wrap(*args, **kwargs):
            def try_func():
                try:
                    return func(*args, **kwargs)
                finally:
                    if sys.exc_info()[0] is not None and rfum is not None:
                        rfum.logger.exception(
                            f"Error running thread {threading.current_thread().name}"
                        )

            prefix = get_thread_prefix()
            thread = FunctionThread(
                target=try_func, args=[], kwargs={}, name=prefix + thread_name
            )
            thread.start()
            return thread

        wrap.__signature__ = inspect.signature(func)
        wrap.original = func
        return wrap

    # Directly use @new_thread without ending brackets case, e.g. @new_thread
    if callable(arg):
        thread_name = to_camel_case(arg.__name__, divider="_")
        return wrapper(arg)
    # Use @new_thread with ending brackets case, e.g. @new_thread('A'), @new_thread()
    elif arg is None:
        return named_thread
    else:
        thread_name = arg
        return wrapper


def force_non_executor_thread(func: Optional[Callable] = None):
    if RFUMInstance.get_rfum().server.is_on_executor_thread():
        raise RuntimeError("Illegal call from executor thread")
    return func


def get_player_from_src(source: CommandSource):
    return source.player if isinstance(source, PlayerCommandSource) else None


def represent(obj: Any, *, attrs: Optional[dict] = None) -> str:
    """
    Copied from PrimeBackup (https://github.com/TISUnion/PrimeBackup)
    Licensed under LGPL-v3.0
    """
    if attrs is None:
        attrs = {
            name: value for name, value in vars(obj).items() if not name.startswith("_")
        }
    kv = []
    for name, value in attrs.items():
        kv.append(f"{name}={value}")
    return "{}({})".format(type(obj).__name__, ", ".join(kv))


def get_thread_pool_executor(
    max_workers: Optional[int] = None,
    thread_name_prefix: str = "",
    is_apscheduler: bool = False,
    **executor_kwargs,
):
    config = RFUMInstance.get_rfum().config
    max_workers = max_workers or config.get_thread_pool_executor_max_workers()
    plugin_prefix = get_thread_prefix()
    if not thread_name_prefix.startswith(plugin_prefix):
        thread_name_prefix = plugin_prefix + thread_name_prefix
    executor_kwargs["thread_name_prefix"] = thread_name_prefix
    if is_apscheduler:
        return APSchedulerTPE(max_workers=max_workers, pool_kwargs=executor_kwargs)
    else:
        return ConcurrentTPE(max_workers=max_workers, **executor_kwargs)


AnyScheduler = TypeVar("AnyScheduler", bound=BaseScheduler)


def get_scheduler(
    scheduler_cls: Type[AnyScheduler] = BackgroundScheduler,
    prefix: str = "SessionScheduler",
) -> AnyScheduler:
    scheduler = scheduler_cls()
    scheduler.add_executor(
        get_thread_pool_executor(is_apscheduler=True, thread_name_prefix=prefix)
    )
    return scheduler
