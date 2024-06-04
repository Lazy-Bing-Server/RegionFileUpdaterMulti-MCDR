import json
import os.path
import shutil
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from zipfile import ZipFile
from typing import TYPE_CHECKING, Optional, List

from mcdreforged.api.utils import deserialize, serialize, Serializable

from region_file_updater_multi.mcdr_globals import *

if TYPE_CHECKING:
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti


class RFUMFileNotFound(FileNotFoundError):
    pass


class RFUMMetaSavingFailed(Exception):
    pass


class RecycledFile:
    class Metadata(Serializable):
        original_file_path: str
        delete_time: float

        def __str__(self):
            return f"RecycledMetadata[original_file_path='{self.original_file_path}', delete_time={self.delete_time}]"

        def __repr__(self):
            return str(self)

    def __init__(
        self,
        path_in_bin: str,
        rfum: "RegionFileUpdaterMulti",
        lock: Optional[threading.RLock] = None,
    ):
        self.__rfum = rfum
        self.__slot_path = path_in_bin
        self.__meta: Optional[RecycledFile.Metadata] = None
        self.__lock = lock or threading.RLock()
        self.load_metadata()

    def load_metadata(self):
        with self.__lock:
            if not os.path.isfile(self.meta_path):
                return False
            try:
                with open(self.meta_path, "r", encoding="utf8") as f:
                    raw = json.load(f)
                    self.__rfum.verbose(f"Loading metadata: {raw}")
                    self.__meta = deserialize(raw, self.Metadata)
            except Exception as e:
                self.__rfum.verbose(f"[{e.__class__.__name__}] {str(e)}")
                self.__meta = None
            return self.__meta is not None

    @property
    def is_available(self):
        return all(
            [
                os.path.isdir(self.__slot_path),
                self.load_metadata(),
                os.path.exists(self.file_path),
            ]
        )

    @property
    def path_in_bin(self) -> Path:
        return Path(self.__slot_path)

    @property
    def meta_path(self) -> Path:
        return Path(os.path.join(self.__slot_path, RECYCLED_FILE_META))

    @property
    def file_path(self):
        return os.path.join(self.__slot_path, RECYCLED_FILE_NAME)

    @property
    def original_path(self) -> Optional[Path]:
        if self.__meta is None:
            return None
        return Path(self.__meta.original_file_path)

    @property
    def delete_time(self):
        if self.__meta is None:
            return None
        return self.__meta.delete_time

    def save_metadata(self, metadata: Optional["Metadata"] = None):
        with self.__lock:
            if metadata is not None:
                self.__meta = metadata
            try:
                with open(self.meta_path, "w", encoding="utf8") as f:
                    serialized = serialize(metadata)
                    self.__rfum.verbose(f"Saving metadata: {serialized}")
                    json.dump(serialized, f, ensure_ascii=False, indent=4)
            except Exception as e:
                self.__rfum.verbose(f"[{e.__class__.__name__}] {str(e)}")
                self.__meta = None
                return False
            return True

    def restore(self):
        with self.__lock:
            if not self.is_available:
                raise RFUMFileNotFound("Metadata not found")
            self.__rfum.verbose(f"Restoring deleted file with metadata {self.__meta}")
            if os.path.isfile(self.original_path):
                os.remove(self.original_path)
            if os.path.isdir(self.original_path):
                os.removedirs(self.original_path)
            shutil.move(self.file_path, self.original_path)

    def delete(self):
        with self.__lock:
            self.__rfum.verbose(
                f"Removing recycled file {self.__meta} in {self.path_in_bin}"
            )
            if os.path.isdir(self.__slot_path):
                shutil.rmtree(self.__slot_path)

    def __lt__(self, other: "RecycledFile"):
        return self.delete_time < other.delete_time


class FileUtils:
    def __init__(self, recycle_bin_path: str, rfum: "RegionFileUpdaterMulti"):
        self.__rfum = rfum
        self.__lock = threading.RLock()
        self.__internal_count = 0
        self.__path = self.ensure_dir(recycle_bin_path)

    def get_recycled_files(self, reverse_order: bool = False) -> List[RecycledFile]:
        with self.__lock:
            slots = []
            for item in os.listdir(self.__path):
                dir_ = os.path.join(self.__path, item)
                file_slot = RecycledFile(dir_, self.__rfum, self.__lock)
                if file_slot.is_available:
                    slots.append(file_slot)
            return sorted(slots, reverse=reverse_order)

    def empty(self):
        with self.__lock:
            self.delete(self.__path)
            self.__internal_count = 0

    def get_recycled_file_by_original_path(self, original_path: PathLike):
        with self.__lock:
            for recycled_file in self.get_recycled_files():
                if recycled_file.original_path is None:
                    continue
                if os.path.samefile(recycled_file.original_path, original_path):
                    return recycled_file

    def restore(self, original_path: PathLike):
        with self.__lock:
            self.get_recycled_file_by_original_path(original_path).restore()

    def restore_all(self):
        with self.__lock:
            for item in self.get_recycled_files(True):
                item.restore()

    def get_a_temp_dir_path(self):
        with self.__lock:
            files = os.listdir(self.__path)
            while True:
                new_dir_name = str(self.__internal_count)
                self.__internal_count += 1
                if new_dir_name not in files:
                    path = os.path.join(self.__path, new_dir_name)
                    os.makedirs(path)
                    return path

    def recycle(self, target_file: str):
        with self.__lock:
            if not os.path.exists(target_file):
                raise RFUMFileNotFound(target_file)
            dir_path = self.get_a_temp_dir_path()
            meta = RecycledFile.Metadata(
                original_file_path=target_file, delete_time=time.time()
            )
            recycled_file = RecycledFile(dir_path, self.__rfum, self.__lock)
            self.move(target_file, recycled_file.file_path)
            self.__rfum.verbose(f"Saving metadata {meta} to {recycled_file.meta_path}")
            if not recycled_file.save_metadata(meta):
                raise RFUMMetaSavingFailed(recycled_file.meta_path)
            return recycled_file

    @staticmethod
    def delete(target_file: str, allow_not_found: bool = True):
        if os.path.isdir(target_file):
            shutil.rmtree(target_file)
        elif os.path.isfile(target_file):
            os.remove(target_file)
        elif not allow_not_found:
            raise RFUMFileNotFound(target_file)

    def copy(
        self,
        original_file: PathLike,
        target_path: PathLike,
        allow_not_found: bool = False,
        allow_overwrite: bool = True,
        recycle_overwritten_file: bool = True,
    ):
        def delete_target():
            if os.path.exists(target_path):
                if allow_overwrite:
                    if recycle_overwritten_file:
                        self.recycle(target_path)
                    else:
                        self.delete(target_path)
                else:
                    raise FileExistsError(target_path)

        if os.path.isdir(original_file):
            delete_target()
            shutil.copytree(original_file, target_path)
        elif os.path.isfile(original_file):
            delete_target()
            shutil.copy2(original_file, target_path)
        elif not allow_not_found:
            raise RFUMFileNotFound(original_file)

    def move(
        self,
        original_file: str,
        target_path: str,
        allow_not_found: bool = False,
        allow_overwrite: bool = True,
        recycle_overwritten_file: bool = True,
    ):
        self.copy(
            original_file,
            target_path,
            allow_not_found=allow_not_found,
            allow_overwrite=allow_overwrite,
            recycle_overwritten_file=recycle_overwritten_file,
        )
        self.delete(original_file)

    @staticmethod
    def ensure_dir(folder_path: PathLike):
        if not os.path.isdir(folder_path):
            if os.path.isfile(folder_path):
                os.remove(folder_path)
            os.makedirs(folder_path)
        return folder_path

    @staticmethod
    def safe_ensure_dir(folder_path: PathLike):
        if not os.path.isdir(folder_path):
            os.makedirs(folder_path)
        return folder_path

    def lf_read(
        self,
        target_file_path: PathLike,
        *,
        is_bundled: bool = False,
        encoding: str = "utf8",
    ) -> str:
        if is_bundled:
            with self.__rfum.server.open_bundled_file(str(target_file_path)) as f:
                file_string = f.read().decode(encoding)
        else:
            with open(target_file_path, "r", encoding=encoding) as f:
                file_string = f.read()
        return file_string.replace("\r\n", "\n").replace("\r", "\n")

    def list_bundled_file(self, directory_name: str):
        server = self.__rfum.server
        package = SELF_PLUGIN_PACKAGE_PATH
        if server is not None:
            return server.get_plugin_file_path(server.get_self_metadata().id)
        if os.path.isdir(package):
            return os.listdir(os.path.join(package, directory_name))
        with ZipFile(package, "r") as zip_file:
            result = []
            directory_name = directory_name.replace("\\", "/").rstrip("/\\") + "/"
            for file_info in zip_file.infolist():
                # is inside the dir and is directly inside
                if file_info.filename.startswith(directory_name):
                    file_name = file_info.filename.replace(directory_name, "", 1)
                    if len(file_name) > 0 and "/" not in file_name.rstrip("/"):
                        result.append(file_name)
        return result

    @contextmanager
    def safe_write(self, target_file_path: PathLike, *, encoding: str = "utf8"):
        temp_file_path = str(target_file_path) + ".tmp"
        self.delete(temp_file_path)
        with open(temp_file_path, "w", encoding=encoding) as file:
            yield file
        os.replace(temp_file_path, target_file_path)

    def __enter__(self):
        self.empty()
        os.makedirs(self.__path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_tb is not None:
            for item in self.get_recycled_files(reverse_order=True):
                try:
                    item.restore()
                except:
                    pass
        self.empty()
