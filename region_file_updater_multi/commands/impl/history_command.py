from mcdreforged.api.all import *

from region_file_updater_multi.commands.sub_command import AbstractSubCommand
from region_file_updater_multi.commands.tree_constants import *
from region_file_updater_multi.components.list import ListComponent
from region_file_updater_multi.components.misc import (
    get_rfum_comp_prefix,
    datetime_tr,
)
from region_file_updater_multi.mcdr_globals import *


class HistoryCommand(AbstractSubCommand):
    @property
    def is_complex(self) -> bool:
        return False

    @property
    def is_debug_command(self):
        return False

    def add_children_for(self, root_node: AbstractNode):
        return root_node.then(
            self.permed_literal(HISTORY)
            .runs(self.display_history)
            .then(
                self.list_command_factory(self.literal(LIST)).runs(
                    self.list_history_regions
                )
            )
        )

    @property
    def tr_key_prefix(self):
        return TRANSLATION_KEY_PREFIX + f"command.{HISTORY}."

    def display_history(self, source: CommandSource, context: CommandContext):
        current_prefix = context.command.split(" ")[0]
        history = self.rfum.history.data
        if history is None:
            return source.reply(get_rfum_comp_prefix(self.ctr("error.not_recorded")))
        text = [
            self.rtr(f"{HISTORY}.result.title"),
            get_rfum_comp_prefix(
                self.ctr(
                    "result.executor", history.player or self.rfum.rtr("format.console")
                )
            ),
            get_rfum_comp_prefix(
                self.ctr("result.time", datetime_tr(history.timestamp))
            ),
            get_rfum_comp_prefix(
                self.ctr(
                    "result.status",
                    self.rtr(
                        f'{HISTORY}.{"succeeded" if history.is_last_operation_succeeded else "failed"}'
                    ),
                )
            ),
            get_rfum_comp_prefix(self.ctr("result.upstream", history.upstream_name)),
            get_rfum_comp_prefix(
                self.rtr(
                    f"{HISTORY}.result.region_amount",
                    count=len(history.last_operation_mca),
                    button=self.rtr(f"{HISTORY}.result.list_region_button")
                    .c(RAction.run_command, f"{current_prefix} {HISTORY} {LIST}")
                    .h(self.rtr(f"{HISTORY}.result.list_button_hover")),
                )
            ),
        ]
        source.reply(get_rfum_comp_prefix(*text, divider="\n"))

    def list_history_regions(self, source: CommandSource, context: CommandContext):
        page, item_per_page = self.get_list_args(context)
        current_prefix = context.command.split(" ")[0]
        regions = self.rfum.history.data.last_operation_mca

        list_comp = ListComponent(
            regions.items(),
            lambda t: get_rfum_comp_prefix(
                RText(t[0], RColor.aqua).h(
                    self.rtr(
                        f"{LIST}.line.add_hover",
                        t[1] or self.rfum.rtr("format.console"),
                    )
                )
            ),
            self.config.default_item_per_page,
        )
        text = [
            self.rtr(f"{HISTORY}.{LIST}.title"),
            get_rfum_comp_prefix(self.rtr(f"{HISTORY}.{LIST}.amount", len(regions))),
            *list_comp.get_page_line_list(page, item_per_page=item_per_page),
            list_comp.get_page_hint_line(
                page,
                item_per_page=item_per_page,
                command_format=f"{current_prefix} {HISTORY} list "
                + self.get_list_command_args_format(),
            )
        ]
        source.reply(get_rfum_comp_prefix(*text, divider="\n"))
