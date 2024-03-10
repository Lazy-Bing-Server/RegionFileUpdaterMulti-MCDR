from typing import Iterable, Generic, TypeVar, Callable, Optional, List

from mcdreforged.api.all import *


T = TypeVar('T')


class ListComponent(Generic[T]):
    def __init__(self, object_list: Iterable[T], factory: Callable[[T], RTextBase], default_item_per_page: int):
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
        return int(len(self) / item_per_page) + 1

    def get_head_tail_index(self, page: int, item_per_page: Optional[int] = None):
        if page > self.get_max_page(item_per_page):
            raise IndexError('Page index out of range')
        item_per_page = item_per_page or self.__default_item_per_page
        head_index = (page - 1) * item_per_page
        tail_index = page * item_per_page - 1
        if tail_index >= self.length:
            tail_index = self.length
        return head_index, tail_index

    def get_page_rtext(self, page: int, force_refresh: bool = False, item_per_page: Optional[int] = None):
        if force_refresh:
            self.clear_cache()
        return RTextBase.join('\n', self.build(*self.get_head_tail_index(page, item_per_page)))

    @property
    def length(self):
        if self.__length is None:
            self.__length = len(self.__list)
        return self.__length

    def __len__(self):
        return self.length
