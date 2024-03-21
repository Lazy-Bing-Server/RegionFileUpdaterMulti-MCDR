import json
import os
import re
from logging import Logger
from typing import Optional, Union, List, Dict, Callable

from mcdreforged.api.all import *
from ruamel import yaml

from region_file_updater_multi.components.misc import get_rfum_comp_prefix
from region_file_updater_multi.commands.command_manager import CommandManager
from region_file_updater_multi.config import Config
from region_file_updater_multi.group import GroupManager
from region_file_updater_multi.history import History
from region_file_updater_multi.mcdr_globals import *
from region_file_updater_multi.region import RegionUpstreamManager
from region_file_updater_multi.session import CurrentSession
from region_file_updater_multi.utils.file_utils import FileUtils
from region_file_updater_multi.utils.logging import (
    NoColorFormatter,
    attach_file_handler,
    get_datetime_format,
)
from region_file_updater_multi.utils.misc_tools import RFUMInstance
from region_file_updater_multi.commands.impl import *


class RegionFileUpdaterMulti:
    def __init__(self):
        self.server = ServerInterface.psi()
        if SELF_PLUGIN_ID != self.server.get_self_metadata().id:
            raise RuntimeError("Illegal call from outside of RegionFileUpdaterMulti")
        self.__logger = self.server.logger
        RFUMInstance.set_rfum(self)

        self.__file_handler = None
        self.set_log(os.path.join(self.server.get_data_folder(), LOG_FILE))

        self.file_utilities = FileUtils(
            os.path.join(self.get_data_folder(), RECYCLE_BIN_FOLDER), self
        )
        Config.set_rfum(self)
        self.__verbosity = False
        self.config: Config = self.load_config()    # type: ignore[annotation-unchecked]
        self.__set_verbosity(self.config.get_verbosity())
        # sself.verbose(self.config.update_operation.confirm_time_wait)

        self.history = History(os.path.join(self.get_data_folder(), HISTORY_FILE), self)
        self.region_upstream_manager = RegionUpstreamManager.get_instance(self)
        self.current_session = CurrentSession(self)
        self.group_manager = GroupManager(
            os.path.join(self.get_data_folder(), GROUP_FILE), self
        )

        self.command_manager = CommandManager(self)

    def load_config(self):
        self.config = Config.load(self)
        return self.config

    def save_config(self):
        if self.config is None:
            raise ValueError("Trying to save config before load")
        self.config.save(self)

    def get_data_folder(self):
        return self.server.get_data_folder()

    def set_log(self, file_name: str):
        self.unset_log()
        formatter = NoColorFormatter(
            "[%(name)s] [%(asctime)s] [%(threadName)s/%(levelname)s]: %(message)s",
            datefmt=get_datetime_format(self.server),
        )
        self.__file_handler = attach_file_handler(self.logger, file_name, formatter)

    def unset_log(self):
        if self.__file_handler is not None:
            self.logger.removeHandler(self.__file_handler)
        self.__file_handler = None

    @property
    def logger(self) -> Union["MCDReforgedLogger", "Logger"]:
        return self.__logger

    def __set_verbosity(self, verbosity: bool):
        self.__verbosity = verbosity
        if verbosity:
            self.verbose("Verbose mode is enabled")

    def verbose(self, msg: str):
        if isinstance(self.logger, MCDReforgedLogger):
            self.logger.debug(msg, no_check=self.__verbosity)
        else:
            self.logger.debug(msg)

    def htr(
        self,
        translation_key: str,
        *args,
        prefixes: Optional[List[str]] = None,
        suggest_prefix: Optional[str] = None,
        **kwargs,
    ) -> RTextMCDRTranslation:
        prefixes = prefixes or [""]

        def __get_regex_result(line: str):
            pattern = r"(?<=§7){}[\S ]*?(?=§)"
            for prefix in prefixes:
                result = re.search(pattern.format(prefix), line)
                if result is not None:
                    return result
            return None

        def __htr(key: str, *inner_args, **inner_kwargs) -> MessageText:
            nonlocal suggest_prefix
            original = self.ntr(key, *inner_args, **inner_kwargs)
            processed: List[MessageText] = []
            if not isinstance(original, str):
                return key
            for line in original.splitlines():
                result = __get_regex_result(line)
                if result is not None:
                    command = result.group().strip() + " "
                    if suggest_prefix is not None:
                        command = suggest_prefix.strip() + " " + command
                    processed.append(
                        RText(line)
                        .c(RAction.suggest_command, command)
                        .h(self.rtr("help_message.suggest", command))
                    )

                    self.verbose(f'Rich help line: "{line}"')
                    self.verbose(
                        "Suggest prefix: {}".format(
                            f'"{suggest_prefix}"'
                            if isinstance(suggest_prefix, str)
                            else suggest_prefix
                        )
                    )
                    self.verbose(f'Suggest command: "{command}"')
                else:
                    processed.append(line)
            return RTextBase.join("\n", processed)

        return self.rtr(translation_key, *args, **kwargs).set_translator(__htr)

    def rtr(
        self,
        translation_key: str,
        *args,
        _lb_rtr_prefix: str = TRANSLATION_KEY_PREFIX,
        **kwargs,
    ) -> RTextMCDRTranslation:
        if not translation_key.startswith(_lb_rtr_prefix):
            translation_key = f"{_lb_rtr_prefix}{translation_key}"
        return RTextMCDRTranslation(translation_key, *args, **kwargs).set_translator(
            self.ntr
        )

    def ktr(
        self,
        translation_key: str,
        *args,
        _lb_tr_default_fallback: Optional[MessageText] = None,
        _lb_tr_log_error_message: bool = False,
        _lb_rtr_prefix: str = TRANSLATION_KEY_PREFIX,
        **kwargs,
    ) -> RTextMCDRTranslation:
        return self.rtr(
            translation_key,
            *args,
            _lb_rtr_prefix=_lb_rtr_prefix,
            _lb_tr_log_error_message=_lb_tr_log_error_message,
            _lb_tr_default_fallback=_lb_tr_default_fallback or translation_key,
            **kwargs,
        )

    def ntr(
        self,
        translation_key: str,
        *args,
        _mcdr_tr_language: Optional[str] = None,
        _mcdr_tr_allow_failure: bool = True,
        _mcdr_tr_fallback_language: Optional[str] = None,
        _lb_tr_default_fallback: Optional[MessageText] = None,
        _lb_tr_log_error_message: bool = True,
        **kwargs,
    ) -> MessageText:
        try:
            return self.server.tr(
                translation_key,
                *args,
                _mcdr_tr_language=_mcdr_tr_language,
                _mcdr_tr_fallback_language=_mcdr_tr_fallback_language or "en_us",
                _mcdr_tr_allow_failure=False,
                **kwargs,
            )
        except Exception:
            languages = []
            for item in (_mcdr_tr_language, _mcdr_tr_fallback_language):
                if item is not None and item not in languages:
                    languages.append(item)
            language_text = ", ".join(languages)
            if _mcdr_tr_allow_failure:
                if _lb_tr_log_error_message:
                    self.logger.error(
                        f'Error translate text "{translation_key}" to language {language_text}'
                    )
                if _lb_tr_default_fallback is None:
                    return translation_key
                return _lb_tr_default_fallback
            else:
                raise

    def register_event_listeners(self):
        self.server.register_event_listener(
            MCDRPluginEvents.PLUGIN_UNLOADED, lambda *args, **kwargs: self.unset_log()
        )
        self.current_session.register_event_listeners()

    def register_custom_translations(self):
        def translation_filter(mapping: Dict[str, str]):
            ret = {}
            for k, v in mapping.items():
                if k == SELF_PLUGIN_ID or k.startswith(TRANSLATION_KEY_PREFIX):
                    ret[k] = v
                else:
                    self.verbose("Non RFUMulti key found: {}".format(k))
            return ret

        tr_folder = os.path.join(self.get_data_folder(), CUSTOM_TRANSLATION_FOLDER)
        if not os.path.isdir(tr_folder):
            os.makedirs(tr_folder)

        if self.config.load_custom_translation:
            for file in os.listdir(tr_folder):
                path = os.path.join(tr_folder, file)
                if os.path.isfile(path):
                    lang, ext = os.path.splitext(file)
                    data = None
                    if ext in ["yml", "yaml"]:
                        try:
                            with open(path, "r", encoding="utf8") as f:
                                data = yaml.YAML().load(f)
                        except:
                            continue
                    elif ext == "json":
                        try:
                            with open(path, "r", encoding="utf8") as f:
                                data = json.load(f)
                        except:
                            continue
                    if isinstance(data, dict):
                        self.verbose(f"Registered custom translation: {file}")
                        self.server.register_translation(lang, translation_filter(data))

    def reply_reload_message(self, source: CommandSource):
        source.reply(get_rfum_comp_prefix(self.rtr("command.reload.reloaded")))

    def on_load(self, server: "PluginServerInterface", prev_module):
        self.register_custom_translations()
        self.register_event_listeners()

        self.command_manager.add_command(HelpCommand(self))
        self.command_manager.add_command(UpstreamCommand(self))
        self.command_manager.add_command(AddDelCommand(self))
        self.command_manager.add_command(UpdateCommand(self))
        self.command_manager.add_command(HistoryCommand(self))
        self.command_manager.add_command(DebugCommands(self))

        self.command_manager.register()
        for pre in self.command_manager.prefixes:
            server.register_help_message(pre, self.rtr("help_message.mcdr"))
