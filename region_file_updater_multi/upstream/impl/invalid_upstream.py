from typing import TYPE_CHECKING, Optional, Type

from region_file_updater_multi.upstream.abstract_upstream import AbstractUpstream

if TYPE_CHECKING:
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti


class InvalidUpstream(AbstractUpstream):
    @classmethod
    def is_path_valid(cls, *args, **kwargs):
        pass

    @classmethod
    def assert_path_valid(cls, *args, **kwargs):
        pass

    def __init__(
        self, rfum: "RegionFileUpdaterMulti", name: str, file_path: str, world_name: str
    ):
        self.__rfum = rfum
        self.__name = name
        self.__path = file_path
        self.__exc: Optional[BaseException] = None
        self.__world_name = world_name
        self.__original_type: Optional[Type["AbstractUpstream"]] = None

    @property
    def name(self):
        return self.__name

    @property
    def original_type_name(self):
        return self.original_type.__name__

    @property
    def original_type(self):
        return self.__original_type or InvalidUpstream

    def extract_file(self, *args, **kwargs) -> None:
        raise RuntimeError("Illegal call to extract file")

    def set_error_message(self, type_: Type[AbstractUpstream], exc: BaseException):
        self.__exc = exc
        self.__original_type = type_
        return self

    def get_error_message(self):
        return (
            f"[{self.__exc.__class__.__name__}] {str(self.__exc)}"
            or self.__rfum.rtr("error_message.unexpected")
        )
