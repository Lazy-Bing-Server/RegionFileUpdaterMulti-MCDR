import json
import os.path
import threading
from typing import TYPE_CHECKING, Optional, Dict

from region_file_updater_multi.utils.serializer import RFUMSerializable

if TYPE_CHECKING:
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti


class History:
    class HistoryData(RFUMSerializable):
        player: str
        is_last_operation_succeeded: bool
        last_operation_mca: Dict[str, str]

    def __init__(self, path: str, rfum: "RegionFileUpdaterMulti"):
        self.__rfum = rfum
        self.__path = path
        self.__lock = threading.RLock()
        self.__data: Optional[History.HistoryData] = self.load_history()

    @property
    def is_empty(self):
        return self.__data is None

    @property
    def data(self):
        return self.__data

    def load_history(self) -> Optional["HistoryData"]:
        with self.__lock:
            try:
                with open(os.path.join(self.__path), 'r', encoding='utf8') as f:
                    return History.HistoryData.deserialize(json.load(f))
            except (KeyError, ValueError, FileNotFoundError):
                return None

    def save_history(self, data: Optional["History.HistoryData"] = None) -> bool:
        with self.__lock:
            if data is None:
                data = self.__data
            try:
                with open(os.path.join(self.__rfum.server.get_data_folder(), self.__path), 'w', encoding='utf8') as f:
                    json.dump(data.serialize(), f, ensure_ascii=False, indent=4)
            except (KeyError, ValueError):
                return False
            else:
                self.__data = data
                return True

    def record(self, player: str, is_last_operation_succeeded: bool, last_operation_mca: Dict[str, str]):
        with self.__lock:
            self.save_history(self.HistoryData.deserialize(dict(
                player=player,
                is_last_operation_succeeded=is_last_operation_succeeded,
                last_operation_mca=last_operation_mca
            )))
