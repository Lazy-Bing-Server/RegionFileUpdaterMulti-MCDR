import os

from mcdreforged.api.all import *
from typing import TYPE_CHECKING, Union, Callable, Optional, Any, List, Tuple

from region_file_updater_multi.commands.tree_constants import *
from region_file_updater_multi.utils import misc_tools
from region_file_updater_multi.region import Region
from region_file_updater_multi.components.misc import *
from region_file_updater_multi.components.list import ListComponent
from region_file_updater_multi.upstream.abstract_upstream import AbstractUpstream
from region_file_updater_multi.upstream.impl.pb_upstream import PrimeBackupUpstream
from region_file_updater_multi.upstream.impl.invalid_upstream import InvalidUpstream
from region_file_updater_multi.upstream.impl.world_upstream import WorldSaveUpstream
from region_file_updater_multi.commands.nodes import *

if TYPE_CHECKING:
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti


class CommandManager:
    def __init__(self, rfum: "RegionFileUpdaterMulti"):
        self.__rfum = rfum
        self.__builder = SimpleCommandBuilder()
        self.__root = Literal(self.prefixes)

    @property
    def prefixes(self):
        prefixes = self.__rfum.config.command.command_prefix
        if isinstance(prefixes, list):
            return prefixes
        return [prefixes]

    @property
    def server(self):
        return self.__rfum.server

    @property
    def is_debug_commands_enabled(self):
        return self.__rfum.config.get('debug_commands', False)

    @property
    def config(self):
        return self.__rfum.config

    """
    ===== Command CallBack =====
    """

    def rtr(
            self,
            translation_key: str,
            *args,
            _lb_rtr_prefix: str = TRANSLATION_KEY_PREFIX + 'command.',
            **kwargs
    ) -> RTextMCDRTranslation:
        return self.__rfum.rtr(translation_key, *args, _lb_rtr_prefix=_lb_rtr_prefix, **kwargs)

    def htr(
            self,
            translation_key: str,
            *args,
            prefixes: Optional[List[str]] = None,
            suggest_prefix: Optional[str] = None,
            _lb_rtr_prefix: str = TRANSLATION_KEY_PREFIX + 'command.',
            **kwargs
    ) -> RTextMCDRTranslation:
        return self.__rfum.htr(
            translation_key,
            *args,
            prefixes=prefixes,
            suggest_prefix=suggest_prefix,
            _lb_rtr_prefix=_lb_rtr_prefix,
            **kwargs
        )

    # !!rfum
    def plugin_overview(self, source: CommandSource):
        meta = self.__rfum.server.get_self_metadata()
        version = meta.version
        version_str = '.'.join([str(n) for n in version.component]) + '-' + str(version.pre)
        source.reply(self.htr(
            'help.overview',
            plugin_name=meta.name,
            version=version_str,
            pre=self.prefixes[0],
            prefixes=self.prefixes,
            help=HELP,
            upstream=UPSTREAM,
            add=ADD,
            del_=DEL,
            del_all=DEL_ALL,
            list=LIST,
            history=HISTORY,
            group=GROUP,
            update=UPDATE,
            reload=RELOAD
        ))

    def get_list_opt_args_text(self):
        return self.rtr(
                'help.list_opt_args',
                page_num_arg=PAGE_INDEX,
                item_count_arg=ITEM_PER_PAGE,
                default_count=self.config.default_item_per_page)

    # !!rfum upstream
    def help_upstream(self, source: CommandSource, context: CommandContext):
        command = context.command.split(' ')[0] + ' ' + UPSTREAM
        current_upstream = self.__rfum.region_upstream_manager.get_current_upstream()
        text = [
            self.rtr('help.single_help_title', pre=command),
            self.rtr(f'{UPSTREAM}.status.current', current_upstream.name if current_upstream is not None else "None"),
            self.rtr(f'{UPSTREAM}.help.desc', pre=command),
            self.rtr('help.usage_title', pre=command),
            self.rtr('help.command_omitted', pre=command),
            self.htr(f'{UPSTREAM}.help.usage', list=LIST, upstream_name=UPS_NAME, suggest_prefix=command),
            self.rtr('help.optional_arguments_title'),
            self.get_list_opt_args_text(),
        ]
        source.reply(get_rfum_comp_prefix(RTextBase.join('\n', text)))

    # !!rfum help add/del/del-all
    def help_add_del(self, source: CommandSource, context: CommandContext):
        current_prefix = context.command.split(' ')[0]
        command = f'{current_prefix} {ADD}/{DEL}/{DEL_ALL}'
        text = [
            # self.rtr('upstream.help.current', self.__rfum.region_manager.get_current_upstream().name),
            self.rtr('help.single_help_title', pre=command),
            self.rtr(f'add_del.help.desc'),
            self.rtr('help.usage_title'),
            # self.rtr('help.command_omitted', pre=command),
            self.__rfum.htr(f'command.add_del.help.usage',
                            pre=current_prefix,
                            add=ADD,
                            del_=DEL,
                            del_all=DEL_ALL,
                            prefixes=self.prefixes),
            self.rtr('help.arguments_title'),
            self.rtr('add_del.help.args'),
        ]
        source.reply(get_rfum_comp_prefix() + RTextBase.join('\n', text))

    def help_list(self, source: CommandSource, context: CommandContext):
        current_prefix = context.command.split(' ')[0]
        command = f'{current_prefix} {LIST}'
        text = [
            # self.rtr('upstream.help.current', self.__rfum.region_manager.get_current_upstream().name),
            self.rtr('help.single_help_title', pre=command),
            self.rtr(f'{LIST}.help.desc'),
            self.rtr('help.usage_title'),
            # self.rtr('help.command_omitted', pre=command),
            self.htr(f'{LIST}.help.usage',
                            pre=current_prefix,
                            list=LIST,
                            prefixes=self.prefixes),
            self.rtr('help.optional_arguments_title'),
            self.get_list_opt_args_text()
        ]
        source.reply(get_rfum_comp_prefix(RTextBase.join('\n', text)))

    def help_history(self, source: CommandSource, context: CommandContext):
        current_prefix = context.command.split(' ')[0]
        command = f'{current_prefix} {HISTORY}'
        text = [
            # self.rtr('upstream.help.current', self.__rfum.region_manager.get_current_upstream().name),
            self.rtr('help.single_help_title', pre=command),
            self.rtr(f'{HISTORY}.help.desc'),
            self.rtr('help.usage_title'),
            # self.rtr('help.command_omitted', pre=command),
            self.htr(f'{HISTORY}.help.usage',
                     pre=current_prefix,
                     history=HISTORY,
                     prefixes=self.prefixes),
            # self.rtr('help.optional_arguments_title'),
            # self.get_list_opt_args_text()
        ]
        source.reply(get_rfum_comp_prefix(RTextBase.join('\n', text)))

    def help_update(self, source: CommandSource, context: CommandContext):
        current_prefix = context.command.split(' ')[0]
        command = f'{current_prefix} {UPDATE}/{ABORT}/{CONFIRM}'
        duration = get_duration_text(self.config.update_operation.confirm_time_wait.value)
        period_text = self.rtr(f'{UPDATE}.help.update_delay', duration)
        requires_confirm = self.config.update_operation.update_requires_confirm
        text = [
            self.rtr('help.single_help_title', pre=command),
            self.rtr(f'{UPDATE}.help.desc'),
            self.rtr(f'{UPDATE}.help.{"requires_confirm" if requires_confirm else "instantly"}')
        ]
        if requires_confirm:
            text.append(period_text)
        text += [
            self.rtr('help.usage_title'),
            self.htr(f'{UPDATE}.help.usage',
                     pre=current_prefix,
                     update=UPDATE,
                     confirm=CONFIRM,
                     abort=ABORT,
                     prefixes=self.prefixes),
            self.rtr('help.optional_arguments_title'),
            self.rtr(f'{UPDATE}.help.args',
                     period_text='' if requires_confirm else '\n' + period_text, default_duration=duration),
        ]

        source.reply(get_rfum_comp_prefix(RTextBase.join('\n', text)))

    def display_current_upstream(self, source: CommandSource, context: CommandContext):
        current_prefix = context.command.split(' ')[0]
        current_upstream = self.__rfum.region_upstream_manager.get_current_upstream()
        text = [
            self.rtr(f'{UPSTREAM}.status.current', current_upstream.name if current_upstream is not None else "None"),
            self.htr(f'{UPSTREAM}.status.more_detail', pre=current_prefix, upstream=UPSTREAM)
        ]
        source.reply(get_rfum_comp_prefix(RTextBase.join('\n', text)))

    def get_list_args(self, context: CommandContext):
        return context.get(PAGE_INDEX) or 1, context.get(ITEM_PER_PAGE) or self.config.default_item_per_page

    @misc_tools.named_thread
    def list_upstream(self, source: CommandSource, context: CommandContext):
        page, item_per_page = self.get_list_args(context)
        current_cmd_prefix = context.command.split(' ')[0]
        rfum = self.__rfum
        current_upstream = rfum.region_upstream_manager.get_current_upstream()
        current_upstream_name = None if current_upstream is None else current_upstream.name
        rfum.verbose(f'Current upstream: {current_upstream_name}')

        def upstream_line_factory(upstream_item: Tuple[str, AbstractUpstream]):
            name, upstream = upstream_item
            invalid = isinstance(upstream, InvalidUpstream)
            original_type = None
            if isinstance(upstream, InvalidUpstream):
                original_type = upstream.original_type
            line_prefix, color = None, None
            if isinstance(upstream, PrimeBackupUpstream) or original_type is PrimeBackupUpstream:
                line_prefix, color = RText('[P]', RColor.dark_aqua).h(self.rtr(f'{UPSTREAM}.list.ups_prefix.pb_hover')), RColor.aqua
            elif isinstance(upstream, WorldSaveUpstream) or original_type is WorldSaveUpstream:
                line_prefix, color = RText('[W]', RColor.gold).h(self.rtr(f'{UPSTREAM}.list.ups_prefix.ws_hover')), RColor.yellow
            if line_prefix is None or color is None:
                return None
            if invalid:
                line_prefix.set_color(RColor.dark_gray)
                color = RColor.gray

            text = [line_prefix]

            set_button = RText("[>]", RColor.dark_green).h(
                self.rtr(f'{UPSTREAM}.list.set_button.hover', RText(name, color))).c(
                RAction.suggest_command, f'{current_cmd_prefix} {UPSTREAM} set {name}'
            )

            if invalid or name == current_upstream_name:
                cant_set_to_button = RText('[-]', RColor.dark_gray, RStyle.strikethrough)
                if invalid:
                    cant_set_to_button.h(self.rtr(f'{UPSTREAM}.{LIST}.set_button.invalid_hover'))
                else:
                    cant_set_to_button.h(self.rtr(f'{UPSTREAM}.{LIST}.set_button.already_current', name=name))
                text.append(cant_set_to_button)
            else:
                text.append(set_button)

            name_text = RText(name, color)
            styles = []
            if name == current_upstream_name:
                styles.append(RStyle.bold)
            if isinstance(upstream, InvalidUpstream):
                name_text.h(self.rtr(f'{UPSTREAM}.list.fail_msg', upstream.get_error_message()))
                styles.append(RStyle.strikethrough)
            name_text.set_styles(styles)
            text.append(name_text)
            text = get_rfum_comp_prefix(*text, divider=' ')
            rfum.verbose(f'Text: "{text}"')
            rfum.verbose(f'Is InvalidUpstream: {invalid}')
            if invalid:
                rfum.verbose(f'Fail reason: {upstream.get_error_message()}')

            return text

        all_upstreams = rfum.region_upstream_manager.get_sorted_upstreams()
        list_comp = ListComponent(all_upstreams, upstream_line_factory, rfum.config.default_item_per_page)
        max_page = list_comp.get_max_page(item_per_page)
        if page != 1 and page > max_page:
            source.reply(get_rfum_comp_prefix(self.rtr(f'{LIST}.error.page_index_out_of_range').set_color(RColor.red)))
        list_text = list_comp.get_page_rtext(page, item_per_page=item_per_page) if list_comp.length != 0 else get_rfum_comp_prefix()
        valid_upstream_count = len(list(filter(lambda item: not isinstance(item[1], InvalidUpstream), all_upstreams)))

        prev_button = RText('<-')
        if page == 1:
            prev_button.set_color(RColor.dark_gray)
        else:
            prev_button.c(
                RAction.run_command, f'{current_cmd_prefix} {UPSTREAM} {LIST} --page {page - 1} --per-page {item_per_page}'
            ).h(
                self.rtr(f'{LIST}.prev_button.hover')
            )
        next_button = RText('->')
        if page >= list_comp.get_max_page(item_per_page):
            next_button.set_color(RColor.dark_gray)
        else:
            next_button.c(
                RAction.run_command, f'{current_cmd_prefix} {UPSTREAM} {LIST} --page {page - 1} --per-page {item_per_page}'
            ).h(
                self.rtr(f'{LIST}.prev_button.hover')
            )

        full_text = [
            self.rtr(f'{UPSTREAM}.list.title'),
            get_rfum_comp_prefix(self.rtr(f'{UPSTREAM}.list.total_count', all=list_comp.length, valid=valid_upstream_count)),
            list_text,
            get_rfum_comp_prefix(prev_button, f'§d{page}§7/§5{max_page}§r', next_button, divider=' ')
        ]
        source.reply(get_rfum_comp_prefix(*full_text, divider='\n'))

    def set_upstream(self, source: CommandSource, context: CommandContext):
        upstream = context[UPS_NAME]
        try:
            self.config.paths.current_upstream = upstream
            self.__rfum.save_config()
        except Exception as exc:
            source.reply(
                get_rfum_comp_prefix(self.rtr(f'{UPSTREAM}.set.fail', upstream=upstream, exc=str(exc)).set_color(RColor.red))
            )
        else:
            source.reply(get_rfum_comp_prefix(self.rtr(f'{UPSTREAM}.set.success', upstream=upstream)))

    # !!rfum add
    @misc_tools.named_thread
    def add_region_by_player_pos(self, source: PlayerCommandSource):
        pass

    @misc_tools.named_thread
    def add_region(self, source: CommandSource, x: int, z: int, dim: Union[int, str]):
        pass

    # !!rfum del
    @misc_tools.named_thread
    def del_region_with_player_pos(self, source: PlayerCommandSource):
        pass

    @misc_tools.named_thread
    def del_region(self, source: CommandSource, x: int, z: int, dim: Union[int, str]):
        pass

    # !!rfum del-all
    def del_all_region(self, source: CommandSource):
        pass

    # !!rfum list
    def list_region(self, source: CommandSource, page: Optional[int], item_per_page: Optional[int]):
        pass

    # !!rfum update
    def execute_update(self, source: CommandSource, context: CommandContext):
        pass

    # !!rfum confirm
    @misc_tools.named_thread
    def confirm_update(self, source: CommandSource):
        pass

    # !!rfum abort
    def abort_update(self, source: CommandSource):
        pass

    # !!rfum history
    def display_history(self, source: CommandSource):
        pass

    # !!rfum reload
    def reload_self(self, source: CommandSource):
        self.server.reload_plugin(self.server.get_self_metadata().id)
        source.reply(get_rfum_comp_prefix() + self.rtr('reload.reloaded'))

    # !!rfum group
    def help_group(self):
        pass

    def list_group(self, source: CommandSource, page: Optional[int], item_per_page: Optional[int]):
        pass

    def create_group(self, source: CommandSource, new_group_name: str):
        pass

    def delete_group(self, source: CommandSource, group_name: str):
        pass

    def info_group(self, source: CommandSource, group_name: str):
        pass

    def use_group_in_session(self, source: CommandSource, group_name: str):
        pass

    @misc_tools.named_thread
    def expand_group_with_player_pos(self, source: CommandSource, group_name: str):
        pass

    def expand_group(self, source: CommandSource, group_name: str, x: int, z: int, dimension: str):
        pass

    @misc_tools.named_thread
    def contract_group_with_player_pos(self, source: CommandSource, group_name: str):
        pass

    def contract_group(self, source: CommandSource, group_name: str, x: int, y: int, dimension: str):
        pass

    def display_group_protection_status(self, source: CommandSource, group_name: str):
        pass

    def enable_group_protection(self, source: CommandSource, group_name: str):
        pass

    def disable_group_protection(self, source: CommandSource, group_name: str):
        pass

    def display_group_whitelist_status(self, source: CommandSource, group_name: str):
        pass

    def display_group_blacklist_status(self, source: CommandSource, group_name: str):
        pass

    def list_group_whitelist_player(self, source: CommandSource, group_name: str, page: Optional[int], item_per_page: Optional[int]):
        pass

    def list_group_blacklist_player(self, source: CommandSource, group_name: str, page: Optional[int], item_per_page: Optional[int]):
        pass

    def append_player_to_whitelist(self, source: CommandSource, group_name: str, player: str):
        pass

    def append_player_to_blacklist(self, source: CommandSource, group_name: str, player: str):
        pass

    def remove_player_from_whitelist(self, source: CommandSource, group_name: str, player: str):
        pass

    def remove_player_from_blacklist(self, source: CommandSource, group_name: str, player: str):
        pass

    def enable_whitelist(self, source: CommandSource, group_name: str):
        pass

    def disable_whitelist(self, source: CommandSource, group_name: str):
        pass

    def enable_blacklist(self, source: CommandSource, group_name: str):
        pass

    def disable_blacklist(self, source: CommandSource, group_name: str):
        pass

    @misc_tools.named_thread
    def debug_extract_file(self, source: CommandSource, context: CommandContext):
        with self.__rfum.file_utilities:
            file_path = context[TARGET_FILE]
            try:
                self.__rfum.region_upstream_manager.get_current_upstream().extract_file(
                    file_path, os.path.join(self.__rfum.get_data_folder(), DEBUG_TEMP_FOLDER)
                )
            except Exception as exc:
                source.reply(f'Exception: {str(exc)}')
                raise
            else:
                source.reply('success')

    @misc_tools.named_thread
    def debug_extract_region(self, source: CommandSource, context: CommandContext):
        pass

    def build(self) -> Literal:
        rtr, builder, rfum = self.rtr, self.__builder, self.__rfum

        def permission_checker(source: CommandSource, context: CommandContext):
            split_cmd = context.command.split(' ')
            return source.has_permission(rfum.config.command.permission.get(split_cmd[1], 0))

        def perm_denied_text_getter():
            return rtr('error_message.permission_denied')

        def check_permission(literal_name: str):
            return builder.literal(literal_name).requires(permission_checker, perm_denied_text_getter)

        def list_callback(callback: Callable[[CommandSource, Optional[int], Optional[int]], Any]):
            return lambda src, ctx: callback(src, ctx.get(PAGE_INDEX), ctx.get(ITEM_PER_PAGE))

        def attach_help_commands(node: Literal):
            node.then(
                Literal(UPSTREAM).runs(self.help_upstream)
            ).then(
                Literal([ADD, DEL, DEL_ALL]).runs(self.help_add_del)
            ).then(
                Literal(LIST).runs(self.help_list)
            ).then(
                Literal(HISTORY).runs(self.help_history)
            ).then(
                Literal({CONFIRM, ABORT, UPDATE}).runs(self.help_update)
            )
            return node

        builder.command(HELP, self.plugin_overview)  # TODO: more detailed
        builder.literal(HELP).post_process(attach_help_commands)

        # Upstream
        builder.command(UPSTREAM, self.display_current_upstream)
        check_permission(UPSTREAM).post_process(
            lambda node: node.then(  # type: AbstractNode
                list_command_factory(LIST, check_perm=False).runs(self.list_upstream)
            ).then(
                Literal('set').then(
                    QuotableText(UPS_NAME).runs(
                        self.set_upstream
                    ).requires(
                        *rfum.region_upstream_manager.get_upstream_name_checker(UPS_NAME)
                    ).suggests(
                        rfum.region_upstream_manager.get_upstream_name_suggester()
                    )
                )
            )
        )

        # Add / Del
        builder.command(ADD, self.add_region_by_player_pos)
        builder.command(f'{ADD} <{X}> <{Z}> <{DIM}>', lambda src, ctx: self.add_region(src, ctx[X], ctx[Z], ctx[DIM]))
        builder.command(DEL, self.del_region_with_player_pos)
        builder.command(f'{DEL} <{X}> <{Z}> <{DIM}>', lambda src, ctx: self.del_region(src, ctx[X], ctx[Z], ctx[DIM]))

        check_permission(ADD).requires(
            lambda src, ctx: len(ctx.command.split(' ')) != 2 or src.is_player, lambda: rtr('add_del.error.not_a_player'))
        check_permission(DEL).requires(
            lambda src, ctx: len(ctx.command.split(' ')) != 2 or src.is_player, lambda: rtr('add_del.error.not_a_player'))

        # Del all
        builder.command(DEL_ALL, self.del_all_region)
        check_permission(DEL_ALL)

        # List (Perm check is in the end of this method)
        builder.command(LIST, list_callback(self.list_region))

        def attach_update_arguments(node: Literal):
            node.then(CountingLiteral(INSTANTLY, INSTANTLY_COUNT).redirects(node))
            node.then(CountingLiteral(REQUIRES_CONFIRM, REQUIRES_CONFIRM_COUNT).redirects(node))
            return node.then(
                Literal('--confirm-period').then(
                    DurationNode(DURATION).redirects(node)
                )
            )

        # Update
        builder.command(UPDATE, self.execute_update)
        check_permission(UPDATE).post_process(attach_update_arguments)

        # Confirm
        builder.command(CONFIRM, self.confirm_update)
        check_permission(CONFIRM)

        # Abort
        builder.command(ABORT, self.abort_update)
        check_permission(ABORT)

        # History
        builder.command(HISTORY, self.display_history)
        check_permission(HISTORY).requires(
            lambda src, ctx: not self.__rfum.history.is_empty,
            lambda: rtr(f'history.error.not_recorded')
        )

        # Reload
        builder.command(RELOAD, self.reload_self)
        check_permission(RELOAD)

        def get_group_name_node(name: str) -> QuotableText:
            return QuotableText(name).suggests(
                rfum.group_manager.get_group_suggester()
            ).requires(
                lambda src, ctx: rfum.group_manager.is_present(ctx[GROUP_NAME]),
                lambda src, ctx: rtr('group.error.not_found', ctx[GROUP_NAME])
            )

        def set_builder_coordinate_args(b: SimpleCommandBuilder):
            b.arg(X, Integer)
            b.arg(Z, Integer)
            b.arg(DIM, QuotableText).requires(
                lambda src, ctx: ctx[DIM] in rfum.config.paths.dimension_region_folder.keys(),
                lambda src, ctx: rtr('add_del.error.invalid_dimension', ctx[DIM])
            ).suggests(
                lambda: rfum.config.paths.dimension_region_folder.keys()
            ).requires(
                lambda src, ctx: rfum.group_manager.is_region_permitted(src, Region(ctx[X], ctx[Z], ctx[DIM])),
                perm_denied_text_getter
            )

        def attach_group_commands(node: AbstractNode):
            gr_builder = SimpleCommandBuilder()
            gr_builder.command(f'delete <{GROUP_NAME}>', lambda src, ctx: self.delete_group(src, ctx[GROUP_NAME]))
            gr_builder.command(f'info <{GROUP_NAME}>', lambda src, ctx: self.info_group(src, ctx[GROUP_NAME]))
            gr_builder.command(f'{USE} <{GROUP_NAME}>', lambda src, ctx: self.use_group_in_session(src, ctx[GROUP_NAME]))
            gr_builder.command(f"expand <{GROUP_NAME}>",
                               lambda src, ctx: self.expand_group_with_player_pos(src, ctx[GROUP_NAME]))
            gr_builder.command(f"expand <{GROUP_NAME}> <{X}> <{Z}> <{DIM}>",
                               lambda src, ctx: self.expand_group(src, ctx[GROUP_NAME], ctx[X], ctx[Z], ctx[DIM]))
            gr_builder.command(f"contract <{GROUP_NAME}>",
                               lambda src, ctx: self.contract_group_with_player_pos(src, ctx[GROUP_NAME]))
            gr_builder.command(f"contract <{GROUP_NAME}> <{X}> <{Z}> <{DIM}>",
                               lambda src, ctx: self.contract_group(src, ctx[GROUP_NAME], ctx[X], ctx[Z], ctx[DIM]))

            gr_builder.arg(GROUP_NAME, get_group_name_node)
            set_builder_coordinate_args(gr_builder)
            gr_builder.add_children_for(node)

            pr_node = Literal(PROTECT)
            pr_builder = SimpleCommandBuilder()
            pr_builder.command(f"<{GROUP_NAME}>",
                               lambda src, ctx: self.display_group_protection_status(src, ctx[GROUP_NAME]))
            pr_builder.command(f"<{GROUP_NAME}> {ENABLE}",
                               lambda src, ctx: self.enable_group_protection(src, ctx[GROUP_NAME]))
            pr_builder.literal(ENABLE).requires(
                lambda src, ctx: not rfum.group_manager.get_group(ctx[GROUP_NAME]).is_whitelist_enabled,
                lambda: rtr('group.error.already_enabled')
            )
            pr_builder.command(f"<{GROUP_NAME}> {DISABLE}",
                               lambda src, ctx: self.disable_group_protection(src, ctx[GROUP_NAME]))
            pr_builder.literal(DISABLE).requires(
                lambda src, ctx: rfum.group_manager.get_group(ctx[GROUP_NAME]).is_whitelist_enabled,
                lambda: rtr('group.error.already_disabled')
            )
            pr_builder.arg(GROUP_NAME, get_group_name_node)
            pr_builder.add_children_for(pr_node)
            node.then(pr_node)

            return node

        # Group
        builder.command(GROUP, self.help_group)
        builder.command(f"{GROUP} {LIST}",
                        list_callback(self.list_group))
        builder.command(f"{GROUP} create <{NEW_GROUP_NAME}>",
                        lambda src, ctx: self.create_group(src, ctx[NEW_GROUP_NAME]))
        check_permission(GROUP).post_process(attach_group_commands)

        # TODO: Remove
        builder.command(f"{GROUP} delete <{GROUP_NAME}>",
                        lambda src, ctx: self.delete_group(src, ctx[GROUP_NAME]))
        builder.command(f"{GROUP} info <{GROUP_NAME}>",
                        lambda src, ctx: self.info_group(src, ctx[GROUP_NAME]))
        builder.command(f"{GROUP} {USE} <{GROUP_NAME}>",
                        lambda src, ctx: self.use_group_in_session(src, ctx[GROUP_NAME]))
        builder.command(f"{GROUP} expand <{GROUP_NAME}>",
                        lambda src, ctx: self.expand_group_with_player_pos(src, ctx[GROUP_NAME]))
        builder.command(f"{GROUP} expand <{GROUP_NAME}> <{X}> <{Z}> <{DIM}>",
                        lambda src, ctx: self.expand_group(src, ctx[GROUP_NAME], ctx[X], ctx[Z], ctx[DIM]))
        builder.command(f"{GROUP} contract <{GROUP_NAME}>",
                        lambda src, ctx: self.contract_group_with_player_pos(src, ctx[GROUP_NAME]))
        builder.command(f"{GROUP} contract <{GROUP_NAME}> <{X}> <{Z}> <{DIM}>",
                        lambda src, ctx: self.contract_group(src, ctx[GROUP_NAME], ctx[X], ctx[Z], ctx[DIM]))
        builder.command(f"{GROUP} {PROTECT} <{GROUP_NAME}>",
                        lambda src, ctx: self.display_group_protection_status(src, ctx[GROUP_NAME]))
        builder.command(f"{GROUP} {PROTECT} <{GROUP_NAME}> {ENABLE}",
                        lambda src, ctx: self.enable_group_protection(src, ctx[GROUP_NAME]))
        builder.command(f"{GROUP} {PROTECT} <{GROUP_NAME}> {DISABLE}",
                        lambda src, ctx: self.disable_group_protection(src, ctx[GROUP_NAME]))
        builder.command(f"{GROUP} {WHITELIST} <{GROUP_NAME}>",
                        lambda src, ctx: self.display_group_whitelist_status(src, ctx[GROUP_NAME]))
        builder.command(f"{GROUP} {WHITELIST} <{GROUP_NAME}> list",
                        lambda src, ctx: self.list_group_whitelist_player(
                            src, ctx[GROUP_NAME], ctx.get(PAGE_INDEX), ctx.get(ITEM_PER_PAGE)))
        builder.command(f"{GROUP} {WHITELIST} <{GROUP_NAME}> append <{PLAYER_TBWL}>",
                        lambda src, ctx: self.append_player_to_whitelist(src, ctx[GROUP_NAME], ctx[PLAYER_TBWL]))
        builder.command(f"{GROUP} {WHITELIST} <{GROUP_NAME}> remove <{WLED_PLAYER}>",
                        lambda src, ctx: self.remove_player_from_whitelist(src, ctx[GROUP_NAME], ctx[WLED_PLAYER]))
        builder.command(f"{GROUP} {WHITELIST} <{GROUP_NAME}> {ENABLE}",
                        lambda src, ctx: self.enable_whitelist(src, ctx[GROUP_NAME]))
        builder.command(f"{GROUP} {WHITELIST} <{GROUP_NAME}> {DISABLE}",
                        lambda src, ctx: self.disable_whitelist(src, ctx[GROUP_NAME]))
        builder.command(f"{GROUP} {BLACKLIST} <{GROUP_NAME}>",
                        lambda src, ctx: self.display_group_blacklist_status(src, ctx[GROUP_NAME]))
        builder.command(f"{GROUP} {BLACKLIST} <{GROUP_NAME}> list",
                        lambda src, ctx: self.list_group_blacklist_player(
                            src, ctx[GROUP_NAME], ctx.get(PAGE_INDEX), ctx.get(ITEM_PER_PAGE)))
        builder.command(f"{GROUP} {BLACKLIST} <{GROUP_NAME}> append <{PLAYER_TBBL}>",
                        lambda src, ctx: self.append_player_to_blacklist(src, ctx[GROUP_NAME], ctx[PLAYER_TBBL]))
        builder.command(f"{GROUP} {BLACKLIST} <{GROUP_NAME}> remove <{BLED_PLAYER}>",
                        lambda src, ctx: self.remove_player_from_blacklist(src, ctx[GROUP_NAME], ctx[BLED_PLAYER]))
        builder.command(f"{GROUP} {BLACKLIST} <{GROUP_NAME}> {ENABLE}",
                        lambda src, ctx: self.enable_blacklist(src, ctx[GROUP_NAME]))
        builder.command(f"{GROUP} {BLACKLIST} <{GROUP_NAME}> {DISABLE}",
                        lambda src, ctx: self.disable_blacklist(src, ctx[GROUP_NAME]))

        def status_checker(source: CommandSource, context: CommandContext, is_to_enable: bool) -> bool:
            args = context.command.split(' ')
            enabled = None
            if args[1] == GROUP:
                group = rfum.group_manager.get_group(context[GROUP_NAME])
                group_action_literal = args[2]
                if group_action_literal == PROTECT:
                    enabled = group.is_protection_enabled
                elif group_action_literal == WHITELIST:
                    enabled = group.is_whitelist_enabled
                elif group_action_literal == BLACKLIST:
                    enabled = group.is_blacklist_enabled
            if enabled is not None:
                return not enabled if is_to_enable else enabled
            return True

        def get_status_checker(is_to_enable: bool):
            return lambda src, ctx: status_checker(src, ctx, is_to_enable)

        builder.literal(USE).requires(
            lambda src, ctx: rfum.group_manager.get_group(ctx[GROUP_NAME]).is_src_permitted(src),
            perm_denied_text_getter
        )

        builder.arg(GROUP_NAME, QuotableText).suggests(
            rfum.group_manager.get_group_suggester()
        ).requires(
            lambda src, ctx: rfum.group_manager.is_present(ctx[GROUP_NAME]),
            lambda src, ctx: rtr('group.error.not_found', ctx[GROUP_NAME])
        )
        builder.arg(NEW_GROUP_NAME, QuotableText).requires(
            lambda src, ctx: not rfum.group_manager.is_present(ctx[NEW_GROUP_NAME]),
            lambda src, ctx: rtr('group.error.already_exists', ctx[NEW_GROUP_NAME])
        )
        builder.arg(PLAYER_TBWL, QuotableText).requires(
            lambda src, ctx: not rfum.group_manager.get_group(ctx[GROUP_NAME]).is_player_whitelisted(ctx[PLAYER_TBWL])
        )
        builder.arg(WLED_PLAYER, QuotableText).requires(
            lambda src, ctx: rfum.group_manager.get_group(ctx[GROUP_NAME]).is_player_whitelisted(ctx[WLED_PLAYER])
        )
        builder.arg(PLAYER_TBBL, QuotableText).requires(
            lambda src, ctx: not rfum.group_manager.get_group(ctx[GROUP_NAME]).is_player_blacklisted(ctx[PLAYER_TBBL])
        )
        builder.arg(BLED_PLAYER, QuotableText).requires(
            lambda src, ctx: rfum.group_manager.get_group(ctx[GROUP_NAME]).is_player_blacklisted(ctx[BLED_PLAYER])
        )

        builder.literal(ENABLE).requires(
            get_status_checker(True),
            lambda: rtr('group.error.already_enabled')
        )
        builder.literal(DISABLE).requires(
            get_status_checker(False),
            lambda: rtr('group.error.already_disabled')
        )

        set_builder_coordinate_args(builder)

        # General list literal
        def list_command_factory(node_name: Union[str, Iterable[str]], check_perm=True):
            node = Literal(node_name)
            node.then(Literal('--page').then(Integer(PAGE_INDEX).redirects(node)))
            node.then(Literal('--per-page').then(Integer(ITEM_PER_PAGE).redirects(node)))
            if check_perm:
                node.requires(permission_checker, perm_denied_text_getter)
            return node
        builder.literal(LIST, list_command_factory)

        if self.config.get_enable_debug_commands():
            rfum.verbose('Debug commands enabled')
            builder.command(f"{DEBUG} {UPSTREAM} extract file <{TARGET_FILE}>", self.debug_extract_file)
            builder.command(f'{DEBUG} {UPSTREAM} extract region <{X}> <{Z}> <{DIM}>')
            builder.arg(TARGET_FILE, QuotableText)

        builder.add_children_for(self.__root)
        self.__root.print_tree(self.__rfum.verbose)
        return self.__root.runs(self.plugin_overview)

    def register(self) -> None:
        tree = self.build()
        self.__rfum.server.register_command(tree)
