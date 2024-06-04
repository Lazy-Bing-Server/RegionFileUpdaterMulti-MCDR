from mcdreforged.api.all import *

from region_file_updater_multi.components.misc import (
    get_rfum_comp_prefix,
    get_duration_text,
)
from region_file_updater_multi.commands.sub_command import AbstractSubCommand
from region_file_updater_multi.mcdr_globals import *
from region_file_updater_multi.commands.tree_constants import *


class HelpCommand(AbstractSubCommand):
    @property
    def is_complex(self) -> bool:
        return False

    @property
    def is_debug_command(self):
        return False

    def add_children_for(self, root_node: AbstractNode):
        _Literal = self.literal
        node = _Literal(HELP).runs(self.command_manager.plugin_overview)
        node.then(_Literal(UPSTREAM).runs(self.help_upstream)).then(
            _Literal([ADD, DEL, DEL_ALL]).runs(self.help_add_del)
        ).then(_Literal(LIST).runs(self.help_list)).then(
            _Literal(HISTORY).runs(self.help_history)
        ).then(_Literal({CONFIRM, ABORT, UPDATE}).runs(self.help_update)).then(
            _Literal(GROUP).runs(self.help_group)
        )
        return root_node.then(node)

    @property
    def tr_key_prefix(self):
        return TRANSLATION_KEY_PREFIX + f"command.{HELP}."

    def get_list_opt_args_text(self):
        return self.ctr(
            "list_opt_args",
            page_num_arg=PAGE_INDEX,
            item_count_arg=ITEM_PER_PAGE,
            default_count=self.config.default_item_per_page,
        )

    # !!rfum upstream
    def help_upstream(self, source: CommandSource, context: CommandContext):
        command = context.command.split(" ")[0] + " " + UPSTREAM
        current_upstream = self.rfum.region_upstream_manager.get_current_upstream()
        text = [
            self.rtr("help.single_help_title", pre=command),
            self.rtr(
                f"{UPSTREAM}.status.current",
                current_upstream.name if current_upstream is not None else "None",
            ),
            self.rtr(f"{UPSTREAM}.help.desc", pre=command),
            self.rtr("help.usage_title", pre=command),
            self.rtr("help.command_omitted", pre=command),
            self.htr(
                f"{UPSTREAM}.help.usage",
                list=LIST,
                upstream_name=UPS_NAME,
                suggest_prefix=command,
            ),
            self.rtr("help.optional_arguments_title"),
            self.get_list_opt_args_text(),
        ]
        source.reply(get_rfum_comp_prefix(RTextBase.join("\n", text)))

    # !!rfum help add/del/del-all
    def help_add_del(self, source: CommandSource, context: CommandContext):
        current_prefix = context.command.split(" ")[0]
        command = f"{current_prefix} {ADD}/{DEL}/{DEL_ALL}"
        text = [
            self.rtr("help.single_help_title", pre=command),
            self.rtr(f"{ADD}_{DEL}.help.desc"),
            self.rtr("help.usage_title"),
            self.htr(
                f"command.{ADD}_{DEL}.help.usage",
                pre=current_prefix,
                add=ADD,
                del_=DEL,
                del_all=DEL_ALL,
                prefixes=self.prefixes,
            ),
            self.rtr("help.arguments_title"),
            self.rtr("add_del.help.args"),
        ]
        source.reply(get_rfum_comp_prefix() + RTextBase.join("\n", text))

    def help_list(self, source: CommandSource, context: CommandContext):
        current_prefix = context.command.split(" ")[0]
        command = f"{current_prefix} {LIST}"
        text = [
            self.rtr("help.single_help_title", pre=command),
            self.rtr(f"{LIST}.help.desc"),
            self.rtr("help.usage_title"),
            # self.rtr('help.command_omitted', pre=command),
            self.htr(
                f"{LIST}.help.usage",
                pre=current_prefix,
                list=LIST,
                prefixes=self.prefixes,
            ),
            self.rtr("help.optional_arguments_title"),
            self.get_list_opt_args_text(),
        ]
        source.reply(get_rfum_comp_prefix(RTextBase.join("\n", text)))

    def help_history(self, source: CommandSource, context: CommandContext):
        current_prefix = context.command.split(" ")[0]
        command = f"{current_prefix} {HISTORY}"
        text = [
            self.rtr("help.single_help_title", pre=command),
            self.rtr(f"{HISTORY}.help.desc"),
            self.rtr("help.usage_title"),
            self.htr(
                f"{HISTORY}.help.usage",
                pre=current_prefix,
                history=HISTORY,
                prefixes=self.prefixes,
            ),
            self.rtr("help.optional_arguments_title"),
            self.get_list_opt_args_text(),
        ]
        source.reply(get_rfum_comp_prefix(RTextBase.join("\n", text)))

    def help_update(self, source: CommandSource, context: CommandContext):
        current_prefix = context.command.split(" ")[0]
        command = f"{current_prefix} {UPDATE}/{ABORT}/{CONFIRM}"
        duration = get_duration_text(
            self.config.update_operation.confirm_time_wait.value
        )
        period_text = self.rtr(f"{UPDATE}.help.update_delay", duration)
        requires_confirm = self.config.update_operation.update_requires_confirm
        text = [
            self.rtr("help.single_help_title", pre=command),
            self.rtr(f"{UPDATE}.help.desc"),
            self.rtr(
                f'{UPDATE}.help.{"requires_confirm" if requires_confirm else "instantly"}'
            ),
        ]
        if requires_confirm:
            text.append(period_text)
        text += [
            self.rtr("help.usage_title"),
            self.htr(
                f"{UPDATE}.help.usage",
                pre=current_prefix,
                update=UPDATE,
                confirm=CONFIRM,
                abort=ABORT,
                prefixes=self.prefixes,
            ),
            self.rtr("help.optional_arguments_title"),
            self.rtr(
                f"{UPDATE}.help.args",
                period_text="" if requires_confirm else "\n" + period_text,
                default_duration=duration,
                instantly=INSTANTLY,
                requires_confirm=REQUIRES_CONFIRM,
                confirm_time_wait=CONFIRM_TIME_WAIT,
            ),
        ]

        source.reply(get_rfum_comp_prefix(RTextBase.join("\n", text)))

    def help_group(self, source: CommandSource, context: CommandContext):
        command = context.command.split(" ")[0] + " " + GROUP
        text = [
            self.rtr("help.single_help_title", pre=command),
            self.rtr(f"{GROUP}.help.desc", pre=command),
            self.rtr("help.usage_title", pre=command),
            self.rtr("help.command_omitted", pre=command),
            self.htr(
                f"{GROUP}.help.usage",
                list=LIST,
                upstream_name=UPS_NAME,
                suggest_prefix=command,
            ),
            # self.rtr(f"{GROUP}.help.list_usage"),
            self.ctr("arguments_title"),
            self.rtr(f"{ADD}_{DEL}.{HELP}.args"),
            self.ctr("optional_arguments_title"),
            self.get_list_opt_args_text(),
            self.rtr(f"{GROUP}.{HELP}.permission_title"),
            self.rtr(f"{GROUP}.{HELP}.permission_levels"),
        ]
        source.reply(get_rfum_comp_prefix(RTextBase.join("\n", text)))
