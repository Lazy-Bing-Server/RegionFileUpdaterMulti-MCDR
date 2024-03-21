from mcdreforged.api.all import *

from typing import Tuple, Union, Optional

from region_file_updater_multi.components.misc import (
    get_rfum_comp_prefix,
)
from region_file_updater_multi.commands.impl.abc.complex_work_command import (
    ComplexWorkCommand,
)
from region_file_updater_multi.commands.tree_constants import *
from region_file_updater_multi.mcdr_globals import *
from region_file_updater_multi.utils import misc_tools
from region_file_updater_multi.components.list import ListComponent
from region_file_updater_multi.region import Region

from minecraft_data_api import get_player_coordinate, get_player_dimension


class AddDelCommand(ComplexWorkCommand):
    @property
    def is_debug_command(self):
        return False

    def add_children_for(self, root_node: AbstractNode):
        builder = SimpleCommandBuilder()
        builder.command(ADD, self.add_region_by_player_pos)
        builder.command(
            f"{ADD} <{X}> <{Z}> <{DIM}>",
            lambda src, ctx: self.add_region(src, ctx[X], ctx[Z], ctx[DIM]),
        )
        builder.command(DEL, self.del_region_with_player_pos)
        builder.command(
            f"{DEL} <{X}> <{Z}> <{DIM}>",
            lambda src, ctx: self.del_region(src, ctx[X], ctx[Z], ctx[DIM]),
        )

        builder.literal(ADD, self.permed_literal)
        builder.literal(DEL, self.permed_literal)
        self.set_builder_coordinate_args(
            builder, x_f=self.integer, z_f=self.integer, d_f=self.quotable_text
        )

        builder.command(DEL_ALL, self.del_all_region)
        builder.literal(DEL_ALL, self.permed_literal)

        builder.command(LIST, self.list_region)
        builder.literal(LIST, self.permed_literal).post_process(
            self.list_command_factory
        )

        builder.add_children_for(root_node)

    @property
    def tr_key_prefix(self):
        return TRANSLATION_KEY_PREFIX + f"command.{ADD}_{DEL}."

    @staticmethod
    def get_region_from_player(player: str):
        coord = get_player_coordinate(player)
        dim = get_player_dimension(player)
        return Region.from_player_coordinates(coord.x, coord.z, str(dim))

    # !!rfum add
    def __add_region(self, source: CommandSource, region: Region):
        if self.is_session_running(source):
            return
        if region in self.rfum.current_session.get_current_regions().keys():
            return source.reply(get_rfum_comp_prefix(self.ctr("existed", str(region))))
        self.rfum.current_session.add_region(
            region, misc_tools.get_player_from_src(source)
        )
        source.reply(get_rfum_comp_prefix(self.ctr("added", str(region))))

    def add_region_by_player_pos(self, source: CommandSource):
        if not isinstance(source, PlayerCommandSource):
            return source.reply(get_rfum_comp_prefix(self.ctr("error.not_a_player")))
        self.__add_region(
            source, self.get_region_from_player(misc_tools.get_player_from_src(source))
        )

    def add_region(self, source: CommandSource, x: int, z: int, dim: Union[int, str]):
        self.__add_region(source, Region(x, z, str(dim)))

    # !!rfum del
    def __del_region(self, source: CommandSource, region: Region):
        if self.is_session_running(source):
            return
        if region not in self.rfum.current_session.get_current_regions().keys():
            return source.reply(
                get_rfum_comp_prefix(self.ctr("not_added", str(region)))
            )
        self.rfum.current_session.remove_region(region)
        source.reply(get_rfum_comp_prefix(self.ctr("removed", str(region))))

    def del_region_with_player_pos(self, source: CommandSource):
        if not isinstance(source, PlayerCommandSource):
            return source.reply(get_rfum_comp_prefix(self.ctr("error.not_a_player")))
        self.__del_region(
            source, self.get_region_from_player(misc_tools.get_player_from_src(source))
        )

    def del_region(self, source: CommandSource, x: int, z: int, dim: Union[int, str]):
        self.__del_region(source, Region(x, z, str(dim)))

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
        list_text = list_comp.get_page_rtext(page, item_per_page=item_per_page)
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
        ]
        if list_text is not None:
            full_text.append(list_text)
        full_text.append(
            list_comp.get_page_hint_line(
                page,
                item_per_page=item_per_page,
                command_format=f"{current_prefix} {LIST} "
                + self.get_list_command_args_format(),
            )
        )
        source.reply(get_rfum_comp_prefix(*full_text, divider="\n"))
