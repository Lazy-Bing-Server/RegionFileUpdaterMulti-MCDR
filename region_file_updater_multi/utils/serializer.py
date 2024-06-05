import os
import shutil
from typing import List, Optional, Tuple, get_origin, Type, Any, TYPE_CHECKING

from mcdreforged.api.utils import Serializable, deserialize, serialize
from ruamel import yaml

from region_file_updater_multi.mcdr_globals import *

if TYPE_CHECKING:
    import io
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti


class RFUMSerializable(Serializable):
    def get(self, key: str, default_value: Any = None):
        if key not in self.get_field_annotations().keys():
            return default_value
        return getattr(self, key, default_value)

    def set(self, key: str, value: Any):
        if key not in self.get_field_annotations().keys():
            raise KeyError(key)
        return setattr(self, key, value)


class BlossomSerializable(RFUMSerializable):
    @classmethod
    def _fix_data(
        cls, data: dict, *, father_nodes: Optional[List[str]] = None
    ) -> Tuple[dict, List[str]]:
        needs_save = list()
        annotations = cls.get_field_annotations()
        default_data = cls.get_default().serialize()
        if father_nodes is None:
            father_nodes = []
        fixed_dict = {}

        for key, target_type in annotations.items():
            current_nodes = father_nodes.copy()
            current_nodes.append(key)
            node_name = ".".join(current_nodes)
            if key not in data.keys():
                if key in default_data.keys():
                    needs_save.append(node_name)
                    fixed_dict[key] = default_data[key]
                continue
            value = data[key]

            def fix_blossom(single_type: Type[BlossomSerializable], single_data: dict):
                nonlocal needs_save
                single_data, save_nodes = single_type._fix_data(
                    single_data, father_nodes=current_nodes
                )
                needs_save += save_nodes
                return single_data

            if get_origin(target_type) is None and issubclass(
                target_type, BlossomSerializable
            ):
                value = fix_blossom(target_type, value)
            else:
                try:
                    value = deserialize(value, target_type, error_at_redundancy=True)
                except (ValueError, TypeError):
                    needs_save.append(node_name)
                    if key not in default_data.keys():
                        continue
                    if isinstance(target_type, Serializable):
                        value = target_type.get_default().serialize()
                    else:
                        try:
                            value = target_type(value)
                        except:
                            value = default_data[key]
                else:
                    value = serialize(value)
            fixed_dict[key] = value
        return fixed_dict, needs_save


class ConfigurationBase(BlossomSerializable):
    @staticmethod
    def get_template(
        rfum: "RegionFileUpdaterMulti",
        path: PathLike,
        supress_template_not_found_warning: bool = True,
    ) -> yaml.CommentedMap:
        rt_yaml = yaml.YAML(typ="rt")
        rt_yaml.width = 1048576
        try:
            with rfum.server.open_bundled_file(str(path)) as f:
                return rt_yaml.load(f)
        except Exception as e:
            if not supress_template_not_found_warning or rfum.verbosity:
                rfum.logger.warning("Template not found, is plugin modified?", exc_info=e)
            return yaml.CommentedMap()

    @classmethod
    def load(
        cls,
        rfum: "RegionFileUpdaterMulti",
        file_path: str = CONFIG_FILE,
        encoding: str = "utf8",
        supress_template_not_found_warning: bool = True,
    ):
        def log(
            translation_key,
            *args,
            _lb_rtr_prefix=TRANSLATION_KEY_PREFIX + "config.",
            **kwargs,
        ):
            text = rfum.ktr(
                translation_key, *args, _lb_rtr_prefix=_lb_rtr_prefix, **kwargs
            )
            rfum.logger.info(text)

        safe_yaml = yaml.YAML(typ="safe")
        safe_yaml.width = 1048576

        default_config = cls.get_default().serialize()
        file_utils = rfum.file_utilities
        needs_save = False
        file_path = os.path.join(rfum.get_data_folder(), file_path)

        # Load & Fix data
        try:
            string = file_utils.lf_read(file_path, encoding=encoding)
            read_data: dict = safe_yaml.load(string)
        except:
            # Reading failed, remove current file
            file_utils.delete(file_path)
            config_dict = default_config.copy()
            needs_save = True
            log("Fail to read config file, using default config")
        else:
            # Reading file succeeded, fix data
            config_dict, nodes_require_save = cls._fix_data(read_data)
            if len(nodes_require_save) > 0:
                needs_save = True
                log(
                    "Fixed invalid config keys with default values, please confirm these values: "
                )
                log(", ".join(nodes_require_save))
        try:
            # Deserialize into configuration instance, should have raise no exception in theory
            result_config = cls.deserialize(config_dict)
        except:
            # But if exception is raised, that indicates config definition error
            result_config = cls.get_default()
            needs_save = True
            log("Fail to read config file, using default config")

        if needs_save:
            # Saving config
            result_config.save(
                rfum,
                encoding=encoding,
                supress_template_not_found_warning=supress_template_not_found_warning
            )

        log(
            "server_interface.load_config_simple",
            _lb_rtr_prefix="",
            _lb_tr_default_fallback="Config loaded",
        )
        return result_config

    def save(
        self,
        rfum: "RegionFileUpdaterMulti",
        file_path: PathLike = CONFIG_FILE,
        bundled_template_path: PathLike = SELF_PLUGIN_CFG_TEMPLATE_PATH,
        encoding: str = "utf8",
        supress_template_not_found_warning: bool = True,
    ):
        def log(
            translation_key,
            *args,
            _lb_rtr_prefix=TRANSLATION_KEY_PREFIX + "config.",
            **kwargs,
        ):
            text = rfum.ktr(
                translation_key, *args, _lb_rtr_prefix=_lb_rtr_prefix, **kwargs
            )
            rfum.logger.info(text)

        file_path = os.path.join(rfum.get_data_folder(), file_path)
        config_temp_path = os.path.join(
            os.path.dirname(file_path), f"temp_{os.path.basename(file_path)}"
        )
        file_utils = rfum.file_utilities

        rt_yaml = yaml.YAML(typ="rt")
        safe_yaml = yaml.YAML(typ="safe")
        for item in (rt_yaml, safe_yaml):  # type: yaml.YAML
            item.width = 1048576
            item.indent(2, 2, 2)

        if os.path.isdir(file_path):
            shutil.rmtree(file_path)

        def _save(safe_dump: bool = False):
            if os.path.exists(config_temp_path):
                file_utils.delete(config_temp_path)

            config_content = self.serialize()
            if safe_dump:
                with file_utils.safe_write(file_path, encoding=encoding) as f:  # type: io.StringIO
                    safe_yaml.dump(config_content, f)
                rfum.logger.warning(
                    "Validation during config file saving failed, saved without original format"
                )
            else:
                formatted_config: yaml.CommentedMap
                if os.path.isfile(file_path):
                    formatted_config = rt_yaml.load(
                        file_utils.lf_read(file_path, encoding=encoding)
                    )
                else:
                    formatted_config = self.get_template(rfum, bundled_template_path)
                for key, value in config_content.items():
                    formatted_config[key] = value
                with file_utils.safe_write(config_temp_path, encoding=encoding) as f:  # type: io.StringIO
                    rt_yaml.dump(formatted_config, f)
                try:
                    self.deserialize(
                        safe_yaml.load(
                            file_utils.lf_read(config_temp_path, encoding=encoding)
                        )
                    )
                except (TypeError, ValueError):
                    log(
                        "Attempting saving config with original file format due to validation failure while "
                        + "attempting saving config and keep local config file format"
                    )
                    log(
                        "There may be mistakes in original config file format, please contact plugin maintainer"
                    )
                    _save(safe_dump=True)
                else:
                    os.replace(config_temp_path, file_path)

        _save()
