import sys
import threading
from typing import Callable, Any
from abc import ABC

from mcdreforged.api.event import MCDRPluginEvents

from region_file_updater_multi.commands.sub_command import AbstractSubCommand
from region_file_updater_multi.utils.misc_tools import get_thread_pool_executor
from concurrent.futures.thread import ThreadPoolExecutor


class ComplexWorkCommand(AbstractSubCommand, ABC):
    def __init__(self, rfum):
        super().__init__(rfum)
        self.__pool_executor: ThreadPoolExecutor = get_thread_pool_executor(    # type: ignore[annotation-unchecked]
            thread_name_prefix=self.__class__.__name__
        )

    def register_event_listener(self):
        self.rfum.server.register_event_listener(
            MCDRPluginEvents.PLUGIN_UNLOADED,
            lambda *args, **kwargs: self.__pool_executor.shutdown(),
        )

    def execute(self, func: Callable[[], Any]):
        self.verbose("Executing command in thread pool")

        def callback():
            try:
                func()
            finally:
                if sys.exc_info()[0] is None:
                    return
                self.logger.exception(
                    f"Unexpected error occurred in thread {threading.current_thread().name}"
                )

        self.__pool_executor.submit(callback)
