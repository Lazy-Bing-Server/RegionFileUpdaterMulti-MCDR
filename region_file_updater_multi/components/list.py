from typing import Iterable, Generic, TypeVar, Callable, Optional, List
from math import ceil

from mcdreforged.api.all import *

from region_file_updater_multi.commands.tree_constants import LIST
from region_file_updater_multi.utils.misc_tools import RFUMInstance
from region_file_updater_multi.components.misc import get_rfum_comp_prefix


T = TypeVar("T")


class ListComponent(Generic[T]):
    def __init__(
        self,
        object_list: Iterable[T],
        factory: Callable[[T], RTextBase],
        default_item_per_page: int,
    ):
        self.__list = list(object_list)
        self.__factory = factory
        self.__length = None
        self.__default_item_per_page = default_item_per_page
        self.__cached_lines: Optional[List[RTextBase]] = None

    def build(self, head: Optional[int] = None, tail: Optional[int] = None):
        if self.__cached_lines is None:
            self.__cached_lines = []
            for item in self.__list[head:tail]:
                line = self.__factory(item)
                if line is not None:
                    self.__cached_lines.append(line)
        return self.__cached_lines

    def clear_cache(self):
        self.__length = None
        self.__cached_lines = None

    def get_max_page(self, item_per_page: Optional[int] = None):
        item_per_page = item_per_page or self.__default_item_per_page
        return ceil(len(self) / item_per_page)

    def get_head_tail_index(self, page: int, item_per_page: Optional[int] = None):
        if page > self.get_max_page(item_per_page):
            raise IndexError("Page index out of range")
        item_per_page = item_per_page or self.__default_item_per_page
        head_index = (page - 1) * item_per_page
        tail_index = head_index + item_per_page
        if tail_index >= self.length:
            tail_index = self.length
        RFUMInstance.get_rfum().verbose(f"Page: {page} Item per page: {item_per_page}")
        RFUMInstance.get_rfum().verbose(f"Head: {head_index} Tail: {tail_index}")
        return head_index, tail_index

    def get_page_rtext(
        self,
        page: int,
        force_refresh: bool = False,
        item_per_page: Optional[int] = None,
    ):
        if force_refresh:
            self.clear_cache()
        if page > self.get_max_page(item_per_page=item_per_page):
            return None
        text_list = self.build(*self.get_head_tail_index(page, item_per_page))
        return RTextBase.join("\n", text_list)

    def get_page_hint_line(
        self,
        page: int,
        item_per_page: Optional[int] = None,
        command_format: Optional[str] = None,
        action: RAction = RAction.run_command,
    ):
        rfum = RFUMInstance.get_rfum()
        item_per_page = item_per_page or self.__default_item_per_page
        max_page = self.get_max_page(item_per_page)
        prev_button = RText("<-")
        if page == 1:
            prev_button.set_color(RColor.dark_gray)
        elif command_format is not None:
            prev_button.c(
                action,
                str(command_format).format(page=page - 1, item_per_page=item_per_page),
            ).h(rfum.rtr(f"command.{LIST}.prev_button.hover"))
        next_button = RText("->")
        if page >= max_page:
            next_button.set_color(RColor.dark_gray)
        elif command_format is not None:
            next_button.c(
                action,
                str(command_format).format(page=page + 1, item_per_page=item_per_page),
            ).h(rfum.rtr(f"command.{LIST}.prev_button.hover"))
        return get_rfum_comp_prefix(
            prev_button, f"§d{page}§7/§5{max_page}§r", next_button, divider=" "
        )

    @property
    def length(self):
        if self.__length is None:
            self.__length = len(self.__list)
        return self.__length

    def __len__(self):
        return self.length
