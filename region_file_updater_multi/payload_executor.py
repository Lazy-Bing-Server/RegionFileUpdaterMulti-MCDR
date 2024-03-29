import sys
import threading
from concurrent.futures.thread import ThreadPoolExecutor
from queue import Queue, Empty
from typing import Any, TYPE_CHECKING, Callable

from mcdreforged.api.all import *

from region_file_updater_multi.utils.misc_tools import (
    named_thread,
    get_thread_pool_executor,
)

if TYPE_CHECKING:
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti


class PayloadExecutor:
    def __init__(self, rfum: "RegionFileUpdaterMulti"):
        self.__rfum = rfum
        self.__work_queue: Queue[Callable[[], Any]] = Queue()
        self.__tick_lock = threading.RLock()
        self.__keep_running = True
        self.__pool_executor: ThreadPoolExecutor = get_thread_pool_executor(  # type: ignore[annotation-unchecked]
            thread_name_prefix="ComplexPayloadExecutor"
        )
        self.__thread = None
        self.__start()

    def __start(self):
        @named_thread("PayloadExecutor")
        def main_loop():
            while True:
                self.__tick()
                if not self.__keep_running:
                    name = threading.current_thread().name
                    self.__rfum.verbose(f"{name} thread terminated")
                    break
            self.__thread = None

        if self.is_normal:
            raise RuntimeError("Payload executor already running")
        self.__thread: FunctionThread = main_loop()  # type: ignore[annotation-unchecked]
        return self.__thread

    def __tick(self):
        with self.__tick_lock:
            try:
                callback = self.__work_queue.get(block=True, timeout=0.01)
            except Empty:
                pass
            else:
                self.__rfum.verbose("PayloadExecutor executing callback...")
                try:
                    callback()
                finally:
                    if sys.exc_info()[0] is not None:
                        threading.current_thread().name += "_Dead"
                        self.__thread = None
                        self.__start()

    def __shutdown(self, *args, **kwargs):
        self.__keep_running = False
        with self.__tick_lock:
            self.__queue = Queue()
        self.__pool_executor.shutdown()

    def add_work(
        self, func: Callable, *args, _payload_add_is_complex: bool = False, **kwargs
    ):
        if not self.is_normal:
            raise RuntimeError("Can't add work to a stopped command executor")
        if not callable(func):
            raise TypeError(f"{func} is not callable")
        if _payload_add_is_complex:
            callback = lambda: self.pool_exec(lambda: func(*args, **kwargs))
        else:
            callback = lambda: func(*args, **kwargs)
        self.__work_queue.put(callback)

    def pool_exec(self, func: Callable[[], Any]):
        self.__rfum.verbose("Executing command in thread pool")

        def callback():
            try:
                func()
            finally:
                if sys.exc_info()[0] is None:
                    return
                self.__rfum.logger.exception(
                    f"Unexpected error occurred in thread {threading.current_thread().name}"
                )

        self.__pool_executor.submit(callback)

    @property
    def is_normal(self):
        return self.__thread is not None

    def register_event_listeners(self):
        self.__rfum.server.register_event_listener(
            MCDRPluginEvents.PLUGIN_UNLOADED, self.__shutdown
        )
