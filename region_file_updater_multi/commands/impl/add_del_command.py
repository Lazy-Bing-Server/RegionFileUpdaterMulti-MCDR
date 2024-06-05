import time

from mcdreforged.api.all import *

from typing import Tuple, Optional

from region_file_updater_multi.components.misc import (
    get_rfum_comp_prefix,
)
from region_file_updater_multi.commands.sub_command import AbstractSubCommand
from region_file_updater_multi.commands.tree_constants import *
from region_file_updater_multi.mcdr_globals import *
from region_file_updater_multi.utils import misc_tools
from region_file_updater_multi.components.list import ListComponent
from region_file_updater_multi.region_upstream_manager import Region


class AddDelCommand(AbstractSubCommand):
    @property
    def is_complex(self) -> bool:
        return True

    @property
    def is_debug_command(self):
        return False

    def add_children_for(self, root_node: AbstractNode):
        def attach_supress_warning(node: AbstractNode):
            return node.then(
                self.counting_literal(SUPRESS_WARNING, SUPRESS_WARNING).redirects(node)
            )

        builder = SimpleCommandBuilder()
        builder.command(ADD, self.add_region_by_player_pos)
        builder.command(f"{ADD} {SUPRESS_WARNING}", self.add_region_by_player_pos)
        builder.command(f"{ADD} {GROUP} <{GROUP_NAME}>", self.group_add_region)
        builder.command(
            f"{ADD} {GROUP} <{GROUP_NAME}> {SUPRESS_WARNING}", self.group_add_region
        )
        builder.command(f"{ADD} <{X}> <{Z}> <{DIM}>", self.add_region)
        builder.command(f"{ADD} <{X}> <{Z}> <{DIM}> {SUPRESS_WARNING}", self.add_region)

        builder.command(DEL, self.del_region_with_player_pos)
        builder.command(f"{DEL} {GROUP} <{GROUP_NAME}>", self.group_del_region)
        builder.command(f"{DEL} <{X}> <{Z}> <{DIM}>", self.del_region)

        builder.literal(ADD, self.permed_literal)
        builder.literal(DEL, self.permed_literal)
        builder.literal(
            SUPRESS_WARNING, lambda name: self.counting_literal(name, SUPRESS_WARNING)
        )
        self.set_builder_coordinate_args(
            builder, x_f=self.integer, z_f=self.integer, d_f=self.quotable_text
        )
        builder.arg(GROUP_NAME, self.quotable_text).post_process(attach_supress_warning)

        builder.command(DEL_ALL, self.del_all_region)
        builder.literal(DEL_ALL, self.permed_literal)

        builder.command(LIST, self.list_region)
        builder.literal(LIST, self.permed_literal).post_process(
            self.list_command_factory
        )
        builder.add_children_for(root_node)

    def __batch_add_region(
        self,
        source: CommandSource,
        current_prefix: str,
        *regions: Region,
        supress_warning: bool = False,
    ):
        if self.is_session_running(source):
            return
        current_session = self.rfum.current_session

        succeeded, failed = [], []
        for region in regions:
            if region in current_session.get_current_regions().keys():
                failed.append(region)
            elif (
                self.config.region_protection.check_add_groups
                and self.rfum.group_manager.is_region_permitted(source, region)
            ):
                failed.append(region)
            else:
                self.reply_warning(source, region, supress_warning)
                current_session.add_region(
                    region, misc_tools.get_player_from_src(source)
                )
                succeeded.append(region)
        source.reply(
            get_rfum_comp_prefix(
                self.ctr("batch_add", succeeded=len(succeeded), failed=len(failed)),
                self.rtr(f"{LIST}.{LIST}_hint.text")
                .c(RAction.run_command, f"{current_prefix} {LIST}")
                .h(self.rtr(f"{LIST}.{LIST}_hint.hover")),
                divider=" ",
            )
        )

    def __batch_del_batch(
        self, source: CommandSource, current_prefix: str, *regions: Region
    ):
        if self.is_session_running(source):
            return
        current_session = self.rfum.current_session
        succeeded, failed = [], []
        for region in regions:
            if region not in current_session.get_current_regions().keys():
                failed.append(region)
            elif (
                self.config.region_protection.check_add_groups
                and self.config.region_protection.check_del_operations
                and self.rfum.group_manager.is_region_permitted(source, region)
            ):
                failed.append(region)
            else:
                current_session.remove_region(
                    region, misc_tools.get_player_from_src(source)
                )
                succeeded.append(region)
        source.reply(
            get_rfum_comp_prefix(
                self.ctr("batch_del", succeeded=len(succeeded), failed=len(failed)),
                self.rtr(f"{LIST}.{LIST}_hint.text")
                .c(RAction.run_command, f"{current_prefix} {LIST}")
                .h(self.rtr(f"{LIST}.{LIST}_hint.hover")),
                divider=" ",
            )
        )

    def group_add_region(self, source: CommandSource, context: CommandContext):
        current_prefix = context.command.split(" ")[0]
        group_name = context[GROUP_NAME]
        group = self.rfum.group_manager.get_group(group_name)
        if group is None:
            return source.reply(
                self.rtr(f"{GROUP}.error.not_found", group_name).set_color(RColor.red)
            )
        self.__batch_add_region(source, current_prefix, *group.regions)

    def group_del_region(self, source: CommandSource, context: CommandContext):
        current_prefix = context.command.split(" ")[0]
        group_name = context[GROUP_NAME]
        if not self.rfum.group_manager.is_present(group_name):
            return source.reply(
                self.rtr(f"{GROUP}.error.not_found", group_name).set_color(RColor.red)
            )
        regions = self.rfum.group_manager.get_group(group_name)
        self.__batch_del_batch(source, current_prefix, *regions)

    @property
    def tr_key_prefix(self):
        return TRANSLATION_KEY_PREFIX + f"command.{ADD}_{DEL}."

    def get_ctx_supress_warning(self, context: CommandContext):
        return self.get_ctx_flag(context, SUPRESS_WARNING)

    def reply_warning(
        self, source: CommandSource, region: Region, supress_warning: bool
    ):
        if supress_warning:
            return
        groups = list(self.rfum.group_manager.get_group_by_region(region))
        if len(groups) <= 0:
            return
        head = groups[:3] if len(groups) > 3 else groups
        head_text = "§f, §r".join([f"§b{item.name}§r" for item in head])
        if len(groups) > 3:
            head_text += "..."
        source.reply(
            get_rfum_comp_prefix(
                self.ctr("group_warning", region).set_color(RColor.yellow),
                get_rfum_comp_prefix(head_text),
                get_rfum_comp_prefix(
                    self.ctr("warn_count", len(groups)).set_color(RColor.yellow)
                ),
                divider="\n",
            )
        )

    # !!rfum add
    def __add_region(
        self, source: CommandSource, region: Region, supress_warning: bool = False
    ):
        if self.is_session_running(source):
            return
        if region in self.rfum.current_session.get_current_regions().keys():
            return source.reply(get_rfum_comp_prefix(self.ctr("existed", str(region))))
        denied = list(self.rfum.group_manager.get_update_denied_groups(source, region))
        self.verbose("Banned by: " + str([g.name for g in denied]))
        if len(denied) > 0:
            self.verbose(f"Source {get_rfum_comp_prefix(source)} perm denied")
            return source.reply(
                get_rfum_comp_prefix(self.command_manager.perm_denied_text_getter())
            )
        self.verbose(f"Source {misc_tools.get_player_from_src(source)} allowed")
        self.reply_warning(source, region, supress_warning)
        time.sleep(0.01)
        self.rfum.current_session.add_region(
            region, misc_tools.get_player_from_src(source)
        )
        source.reply(get_rfum_comp_prefix(self.ctr("added", str(region))))

    def add_region_by_player_pos(self, source: CommandSource):
        if not isinstance(source, PlayerCommandSource):
            return source.reply(
                get_rfum_comp_prefix(
                    self.ctr("error.not_a_player").set_color(RColor.red)
                )
            )
        if self.server.get_plugin_instance(MINECRAFT_DATA_API) is None:
            return source.reply(
                self.ctr("error.api_not_installed").set_color(RColor.red)
            )
        self.__add_region(
            source, self.get_region_from_player(misc_tools.get_player_from_src(source))
        )

    def add_region(self, source: CommandSource, context: CommandContext):
        self.__add_region(
            source,
            Region(*self.get_ctx_coordinates(context)),
            supress_warning=self.get_ctx_supress_warning(context),
        )

    # !!rfum del
    def __del_region(self, source: CommandSource, region: Region):
        if self.is_session_running(source):
            return
        if region not in self.rfum.current_session.get_current_regions().keys():
            return source.reply(
                get_rfum_comp_prefix(self.ctr("not_added", str(region)))
            )
        if (
            self.config.region_protection.check_del_operations
            and not self.rfum.group_manager.is_region_permitted(source, region)
        ):
            return source.reply(
                get_rfum_comp_prefix(self.command_manager.perm_denied_text_getter())
            )
        self.rfum.current_session.remove_region(
            region, misc_tools.get_player_from_src(source)
        )
        source.reply(get_rfum_comp_prefix(self.ctr("removed", str(region))))

    def del_region_with_player_pos(self, source: CommandSource):
        if not isinstance(source, PlayerCommandSource):
            return source.reply(
                get_rfum_comp_prefix(
                    self.ctr("error.not_a_player").set_color(RColor.red)
                )
            )
        if self.server.get_plugin_instance(MINECRAFT_DATA_API) is None:
            return source.reply(
                self.ctr("error.api_not_installed").set_color(RColor.red)
            )
        self.__del_region(
            source, self.get_region_from_player(misc_tools.get_player_from_src(source))
        )

    def del_region(self, source: CommandSource, context: CommandContext):
        self.__del_region(source, Region(*self.get_ctx_coordinates(context)))

    # !!rfum del-all
    def del_all_region(self, source: CommandSource):
        if len(self.rfum.current_session.get_current_regions()) == 0:
            source.reply(
                get_rfum_comp_prefix(
                    self.rtr(f"{UPDATE}.error.list_empty").set_color(RColor.red)
                )
            )
            return
        if self.rfum.current_session.is_session_running:
            source.reply(
                get_rfum_comp_prefix(
                    self.rtr("error_message.session_running").set_color(RColor.red)
                )
            )
            return
        self.rfum.current_session.remove_all_regions()
        source.reply(get_rfum_comp_prefix(self.ctr("removed_all")))

    # !!rfum list
    def list_region(self, source: CommandSource, context: CommandContext):
        page, item_per_page = self.get_list_args(context)
        current_prefix = context.command.split(" ")[0]
        rfum = self.rfum

        def region_line_factory(region_tuple: Tuple[Region, Optional[str]]):
            region, player = region_tuple
            region_text = str(region)
            line = [
                RText("[x]", RColor.red, RStyle.bold)
                .c(
                    RAction.suggest_command,
                    f"{current_prefix} {DEL} {region.x} {region.z} {region.dim}",
                )
                .h(self.rtr(f"{LIST}.line.del_hover")),
                RText(region_text, RColor.aqua).h(
                    self.rtr(
                        f"{LIST}.line.add_hover",
                        player or self.rfum.rtr("format.console"),
                    )
                ),
            ]
            return get_rfum_comp_prefix(*line, divider=" ")

        regions = rfum.current_session.get_current_regions()
        list_comp = ListComponent(
            regions.items(), region_line_factory, self.config.default_item_per_page
        )
        full_text = [
            self.rtr(f"{LIST}.title.text"),
            get_rfum_comp_prefix(
                self.rtr(
                    f"{LIST}.amount",
                    add=RText("[+]", RColor.light_purple, RStyle.bold)
                    .h(self.rtr(f"{LIST}.title.add_hover"))
                    .c(RAction.suggest_command, f"{current_prefix} {ADD} "),
                    amount=len(regions),
                )
            ),
            *list_comp.get_page_line_list(page, item_per_page=item_per_page),
            list_comp.get_page_hint_line(
                page,
                item_per_page=item_per_page,
                command_format=f"{current_prefix} {LIST} "
                + self.get_list_command_args_format(),
            )
        ]
        source.reply(get_rfum_comp_prefix(*full_text, divider="\n"))
