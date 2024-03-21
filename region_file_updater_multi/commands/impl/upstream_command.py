from mcdreforged.api.all import *

from typing import Tuple

from region_file_updater_multi.components.misc import (
    get_rfum_comp_prefix,
)
from region_file_updater_multi.commands.impl.abc.simple_work_command import (
    SimpleWorkCommand,
)
from region_file_updater_multi.commands.tree_constants import *
from region_file_updater_multi.mcdr_globals import *
from region_file_updater_multi.components.list import ListComponent
from region_file_updater_multi.upstream.impl.invalid_upstream import InvalidUpstream
from region_file_updater_multi.upstream.impl.pb_upstream import PrimeBackupUpstream
from region_file_updater_multi.upstream.impl.world_upstream import WorldSaveUpstream
from region_file_updater_multi.upstream.abstract_upstream import AbstractUpstream


class UpstreamCommand(SimpleWorkCommand):
    @property
    def is_debug_command(self):
        return False

    def add_children_for(self, root_node: AbstractNode):
        return root_node.then(
            self.permed_literal(UPSTREAM)
            .runs(self.display_current_upstream)
            .then(
                self.list_command_factory(self.literal(LIST)).runs(self.list_upstream)
            )
            .then(
                self.literal("set").then(
                    self.quotable_text(UPS_NAME)
                    .runs(self.set_upstream)
                    .requires(
                        *self.rfum.region_upstream_manager.get_upstream_name_checker(
                            UPS_NAME
                        )
                    )
                    .suggests(
                        self.rfum.region_upstream_manager.get_upstream_name_suggester()
                    )
                )
            )
        )

    @property
    def tr_key_prefix(self):
        return TRANSLATION_KEY_PREFIX + f"command.{UPSTREAM}."

    def display_current_upstream(self, source: CommandSource, context: CommandContext):
        current_prefix = context.command.split(" ")[0]
        current_upstream = self.rfum.region_upstream_manager.get_current_upstream()
        text = [
            self.rtr(
                f"{UPSTREAM}.status.current",
                current_upstream.name if current_upstream is not None else "None",
            ),
            self.htr(
                f"{UPSTREAM}.status.more_detail", pre=current_prefix, upstream=UPSTREAM
            ),
        ]
        source.reply(get_rfum_comp_prefix(RTextBase.join("\n", text)))

    def list_upstream(self, source: CommandSource, context: CommandContext):
        page, item_per_page = self.get_list_args(context)
        current_cmd_prefix = context.command.split(" ")[0]
        rfum = self.rfum
        current_upstream = rfum.region_upstream_manager.get_current_upstream()
        current_upstream_name = (
            None if current_upstream is None else current_upstream.name
        )
        rfum.verbose(f"Current upstream: {current_upstream_name}")

        def upstream_line_factory(upstream_item: Tuple[str, AbstractUpstream]):
            name, upstream = upstream_item
            invalid = isinstance(upstream, InvalidUpstream)
            original_type = None
            if isinstance(upstream, InvalidUpstream):
                original_type = upstream.original_type
            line_prefix, color = None, None
            if (
                isinstance(upstream, PrimeBackupUpstream)
                or original_type is PrimeBackupUpstream
            ):
                line_prefix = RText("§3[P]§r").h(
                    self.ctr(f"{LIST}.ups_prefix.pb_hover")
                )
            elif (
                isinstance(upstream, WorldSaveUpstream)
                or original_type is WorldSaveUpstream
            ):
                line_prefix = RText("§6[W]§r").h(
                    self.ctr(f"{LIST}.ups_prefix.ws_hover")
                )
            if line_prefix is None:
                return None
            color = RColor.aqua
            if invalid:
                line_prefix.set_color(RColor.dark_gray)
                color = RColor.gray

            text = []

            set_button = (
                RText("[>]", RColor.dark_green)
                .h(self.ctr(f"{LIST}.set_button.hover", RText(name, color)))
                .c(
                    RAction.suggest_command,
                    f"{current_cmd_prefix} {UPSTREAM} set {name}",
                )
            )

            if invalid or name == current_upstream_name:
                cant_set_to_button = RText(
                    "[>]", RColor.dark_gray, RStyle.strikethrough
                )
                if invalid:
                    cant_set_to_button.h(
                        self.ctr(f"{LIST}.set_button.invalid_hover")
                    )
                else:
                    cant_set_to_button.h(
                        self.ctr(f"error.already_current", name=name)
                    )
                text.append(cant_set_to_button)
            else:
                text.append(set_button)
            text.append(line_prefix)

            name_text = RText(name, color)
            styles = []
            if name == current_upstream_name:
                name_text.h(self.rtr(f"{UPSTREAM}.list.current", name))
                styles.append(RStyle.bold)
            if isinstance(upstream, InvalidUpstream):
                name_text.h(
                    self.rtr(f"{UPSTREAM}.list.fail_msg", upstream.get_error_message())
                )
                styles.append(RStyle.strikethrough)
            name_text.set_styles(styles)
            text.append(name_text)
            text = get_rfum_comp_prefix(*text, divider=" ")
            rfum.verbose(f'Text: "{text}"')
            rfum.verbose(f"Is InvalidUpstream: {invalid}")
            if isinstance(upstream, InvalidUpstream):
                rfum.verbose(f"Fail reason: {upstream.get_error_message()}")

            return text

        all_upstreams = rfum.region_upstream_manager.get_sorted_upstreams()
        list_comp = ListComponent(
            all_upstreams, upstream_line_factory, rfum.config.default_item_per_page
        )
        max_page = list_comp.get_max_page(item_per_page)
        if page != 1 and page > max_page:
            source.reply(
                get_rfum_comp_prefix(
                    self.rtr(f"{LIST}.error.page_index_out_of_range").set_color(
                        RColor.red
                    )
                )
            )
        list_text = list_comp.get_page_rtext(page, item_per_page=item_per_page)
        valid_upstream_count = len(
            list(
                filter(
                    lambda item: not isinstance(item[1], InvalidUpstream), all_upstreams
                )
            )
        )

        full_text = [
            self.rtr(f"{UPSTREAM}.list.title"),
            get_rfum_comp_prefix(
                self.rtr(
                    f"{UPSTREAM}.list.total_count",
                    all=list_comp.length,
                    valid=valid_upstream_count,
                )
            ),
        ]
        if list_text is not None:
            full_text.append(list_text)
        full_text.append(
            list_comp.get_page_hint_line(
                page,
                item_per_page=item_per_page,
                command_format=f"{current_cmd_prefix} {UPSTREAM} {LIST} "
                + self.get_list_command_args_format(),
            )
        )
        source.reply(get_rfum_comp_prefix(*full_text, divider="\n"))

    def set_upstream(self, source: CommandSource, context: CommandContext):
        upstream = context[UPS_NAME]
        if self.config.paths.current_upstream == upstream:
            source.reply(
                get_rfum_comp_prefix(
                    self.ctr("error.already_current", name=upstream).set_color(
                        RColor.red
                    )
                )
            )
            return
        try:
            self.config.paths.current_upstream = upstream
            self.rfum.save_config()
        except Exception as exc:
            source.reply(
                get_rfum_comp_prefix(
                    self.rtr(
                        f"{UPSTREAM}.set.fail", upstream=upstream, exc=str(exc)
                    ).set_color(RColor.red)
                )
            )
        else:
            source.reply(
                get_rfum_comp_prefix(
                    self.rtr(f"{UPSTREAM}.set.success", upstream=upstream)
                )
            )
