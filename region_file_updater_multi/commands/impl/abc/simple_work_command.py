from abc import ABC
from typing import Callable, Any

from region_file_updater_multi.commands.sub_command import AbstractSubCommand


class SimpleWorkCommand(AbstractSubCommand, ABC):
    def execute(self, func: Callable[[], Any]):
        return func()
