import threading
from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING, Optional, Dict, Tuple

from mcdreforged.api.all import *

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.job import Job

from region_file_updater_multi.commands.sub_command import AbstractSubCommand
from region_file_updater_multi.commands.tree_constants import *
from region_file_updater_multi.components.list import ListComponent
from region_file_updater_multi.components.misc import (
    get_rfum_comp_prefix,
    group_perm_tr,
    PlayerNameString,
    get_duration_text,
)
from region_file_updater_multi.mcdr_globals import *
from region_file_updater_multi.storage.group import Group, GroupPermission
from region_file_updater_multi.region_upstream_manager import Region
from region_file_updater_multi.utils.misc_tools import (
    get_player_from_src,
    get_scheduler,
)

if TYPE_CHECKING:
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti


class AbstractRepeatConfirmJob(ABC):
    def __init__(
        self,
        group_command: "GroupCommand",
        scheduler: BackgroundScheduler,
        *args,
        **kwargs,
    ):
        self.__group_command = group_command
        self.__scheduler = scheduler
        self.job: Optional[Job] = None
        self.__lock = threading.RLock()

    @property
    def group_command(self):
        return self.__group_command

    @property
    def scheduler(self):
        return self.__scheduler

    @property
    def lock(self):
        return self.__lock

    @property
    def is_running(self):
        with self.lock:
            return self.job is not None

    @abstractmethod
    def timeout_action(self): ...

    def timeout(self):
        with self.lock:
            self.timeout_action()
            self.stop()
            self.group_command.remove_repeat_job(self)

    def start(self):
        with self.lock:
            self.job = self.scheduler.add_job(
                self.timeout, trigger=self.group_command.repeat_timeout_trigger
            )
            if not self.scheduler.running:
                self.scheduler.start()
        self.group_command.verbose(f"Started a job: {str(self)}")

    def stop(self):
        with self.lock:
            if self.is_running:
                self.job.remove()
            self.job = None
        self.group_command.verbose(f"Stopped a job: {str(self)}")

    @abstractmethod
    def modify_permission(self, permission: GroupPermission): ...


class PlayerPermissionConfirmJob(AbstractRepeatConfirmJob):
    def __init__(
        self,
        group_command: "GroupCommand",
        scheduler: BackgroundScheduler,
        player: str,
        permission: GroupPermission,
    ):
        super().__init__(group_command, scheduler)
        self.__player: str = player
        self.__permission: GroupPermission = permission

    @property
    def player(self):
        return self.__player

    @property
    def permission(self):
        return self.__permission

    def modify_permission(self, permission: GroupPermission):
        with self.lock:
            self.stop()
            self.__permission = permission
            self.start()

    def timeout_action(self):
        self.group_command.rfum.server.tell(
            self.__player,
            get_rfum_comp_prefix(self.group_command.ctr("confirm_timeout")),
        )

    def __str__(self):
        return f"PlayerPermission[player={self.player}, perm={self.permission.name}]"


class DefaultPermissionConfirmJob(AbstractRepeatConfirmJob):
    @property
    def permission(self):
        return self.__permission

    def timeout_action(self):
        self.__source.reply(
            get_rfum_comp_prefix(self.group_command.ctr("confirm_timeout"))
        )

    def modify_permission(self, permission: GroupPermission):
        with self.lock:
            self.stop()
            self.__permission = permission
            self.start()

    def __init__(
        self,
        group_command: "GroupCommand",
        scheduler: "BackgroundScheduler",
        source: PlayerCommandSource,
        permission: GroupPermission,
    ):
        super().__init__(group_command, scheduler)
        self.__source = source
        self.__permission = permission

    def __str__(self):
        return (
            f"DefaultPermission[player={get_player_from_src(self.__source)}"
            + f", perm={self.permission.name}]"
        )


class DeletePermissionConfirmJob(AbstractRepeatConfirmJob):
    def timeout_action(self):
        self.group_command.rfum.server.tell(
            self.__player,
            get_rfum_comp_prefix(self.group_command.ctr("confirm_timeout")),
        )

    def modify_permission(self, permission: GroupPermission):
        pass

    def __init__(
        self,
        group_command: "GroupCommand",
        scheduler: "BackgroundScheduler",
        target_player: str,
    ):
        super().__init__(group_command, scheduler)
        self.__player = target_player

    def __str__(self):
        return f"DeletePermission[player={self.__player}"


class GroupCommand(AbstractSubCommand):
    def __init__(self, rfum: "RegionFileUpdaterMulti"):
        super().__init__(rfum)
        self.__scheduler = get_scheduler(
            scheduler_cls=BackgroundScheduler, prefix="GroupPermissionModifyCache"
        )
        self.__scheduler.start()
        self.__player_perm_jobs: Dict[str, PlayerPermissionConfirmJob] = {}
        self.__default_perm_jobs: Dict[str, DefaultPermissionConfirmJob] = {}
        self.__del_perm_jobs: Dict[str, DeletePermissionConfirmJob] = {}

    @property
    def repeat_timeout_trigger(self):
        return IntervalTrigger(
            seconds=self.config.region_protection.permission_modify_repeat_wait_time.value
        )

    @property
    def is_debug_command(self) -> bool:
        return False

    def remove_repeat_job(self, job: AbstractRepeatConfirmJob):
        for p, j in self.__player_perm_jobs.items():
            if job is j:
                del self.__player_perm_jobs[p]
                return

    def group_perm_checker(self, source: CommandSource, context: CommandContext):
        group_name = self.get_group_name(context)
        group = self.rfum.group_manager.get_group(group_name)
        return group is None or group.is_src_permitted(source)

    def add_children_for(self, root_node: AbstractNode) -> Any:
        builder = SimpleCommandBuilder()
        builder.command(GROUP, self.command_preview)
        builder.command(f"{GROUP} {LIST}", self.list_group)
        builder.command(f"{GROUP} {CREATE} <{NEW_GROUP_NAME}>", self.create_group)
        builder.command(f"{GROUP} {DELETE} <{GROUP_NAME}>", self.delete_group)
        builder.command(f"{GROUP} {INFO} <{GROUP_NAME}>", self.info_group)
        builder.command(f"{GROUP} {INFO} <{GROUP_NAME}> {LIST}", self.info_group_list)

        def get_group_node(name: str = GROUP_NAME):
            return self.quotable_text(name).suggests(
                lambda: self.rfum.group_manager.groups.keys()
            )

        def attach_expand_contract_command(node: Literal):
            expand = self.literal(EXPAND)
            expand_sub = get_group_node().runs(self.expand_group_by_player_pos)
            expand_builder = SimpleCommandBuilder()
            expand_builder.command(f"<{X}> <{Z}> <{DIM}>", self.expand_group)
            self.set_builder_coordinate_args(expand_builder)
            expand_builder.add_children_for(expand_sub)

            contract = self.literal(CONTRACT)
            contract_sub = get_group_node().runs(self.contract_group_by_player_pos)
            contract_builder = SimpleCommandBuilder()
            contract_builder.command(f"<{X}> <{Z}> <{DIM}>", self.contract_group)
            self.set_builder_coordinate_args(contract_builder)
            contract_builder.add_children_for(contract_sub)

            return node.then(expand.then(expand_sub)).then(contract.then(contract_sub))

        def attach_permission_command(node: Literal):
            perm_node = self.literal([PERM, PERMISSION])
            group_node = get_group_node()
            perm_builder = SimpleCommandBuilder()

            perm_builder.command(LIST, self.list_player_permission)
            perm_builder.command(
                f"{SET} <{PLAYER}> <{PERM_ENUM}>", self.set_player_permission
            )
            perm_builder.command(
                f"{SET_DEFAULT} <{PERM_ENUM}>", self.set_default_permission
            )
            perm_builder.command(LIST, self.list_player_permission)
            perm_builder.command(f"{DEL} <{PLAYER}>", self.delete_permission)

            perm_builder.literal(DEL, self.literal)
            perm_builder.literal(LIST, self.list_command_factory)
            perm_builder.literal(
                CONFIRM_FLAG, lambda name: self.counting_literal(name, CONFIRM_COUNT)
            )

            def player_suggester(source: CommandSource, context: CommandContext):
                group_name = self.get_group_name(context)
                if group_name is None:
                    return []
                group = self.rfum.group_manager.get_group(group_name)
                if group is None:
                    return []

                player_list = self.rfum.online_players.get_player_list()
                for player in group.get_data(
                    self.rfum.group_manager
                ).player_permission.keys():
                    if player not in player_list:
                        player_list.append(player_list)
                return player_list

            def perm_enum_getter(name: str):
                target_root = self.enumeration(name, GroupPermission)
                return target_root.then(
                    self.counting_literal(CONFIRM_FLAG, CONFIRM_COUNT).redirects(
                        target_root
                    )
                )

            def player_node_process(player_node: QuotableText):
                player_node.suggests(player_suggester)
                player_node.then(
                    self.counting_literal(CONFIRM_FLAG, CONFIRM_COUNT).runs(
                        self.delete_permission
                    )
                )
                return player_node

            perm_builder.arg(PLAYER, self.quotable_text).post_process(
                player_node_process
            )
            perm_builder.arg(PERM_ENUM, perm_enum_getter)

            perm_builder.add_children_for(group_node)
            return node.then(perm_node.then(group_node))

        builder.literal(GROUP, self.permed_literal).post_process(
            attach_expand_contract_command
        ).post_process(attach_permission_command)
        builder.literal(LIST, self.list_command_factory)
        builder.arg(GROUP_NAME, get_group_node)
        builder.arg(NEW_GROUP_NAME, self.quotable_text)

        self.set_builder_coordinate_args(builder)
        builder.add_children_for(root_node)

    @property
    def tr_key_prefix(self) -> str:
        return TRANSLATION_KEY_PREFIX + f"command.{GROUP}."

    @property
    def is_complex(self) -> bool:
        return True

    @staticmethod
    def get_group_name(context: CommandContext):
        return context[GROUP_NAME]

    def group_not_found(self, source: CommandSource, group_name: str):
        source.reply(
            get_rfum_comp_prefix(
                self.ctr("error.not_found", group_name).set_color(RColor.red)
            )
        )

    def is_present(self, group_name: str):
        return self.rfum.group_manager.is_present(group_name)

    def command_preview(self, source: CommandSource, context: CommandContext):
        prefix = context.command.split(" ")[0]
        source.reply(
            self.htr(
                f"{GROUP}.{HELP}.overview",
                pre=prefix,
                help=HELP,
                group=GROUP,
                prefixes=self.prefixes,
            )
        )

    def list_group(self, source: CommandSource, context: CommandContext):
        current_prefix = context.command.split(" ")[0]
        page, item_per_page = self.get_list_args(context)

        def get_group_text(group: Group):
            return get_rfum_comp_prefix(
                RText(group.name, RColor.aqua)
                .h(self.ctr(f"{LIST}.line_hover", group.name))
                .c(RAction.run_command, f"{current_prefix} {GROUP} {INFO} {group.name}")
            )

        list_comp = ListComponent(
            self.rfum.group_manager.groups.values(),
            get_group_text,
            default_item_per_page=self.config.default_item_per_page,
        )

        groups = self.rfum.group_manager.groups
        text = [
            self.ctr(f"{LIST}.title"),
            get_rfum_comp_prefix(
                self.ctr(f"{LIST}.amount", len(groups))
                + " "
                + RText("[+]", RColor.light_purple, RStyle.bold)
                .h(self.ctr(f"{LIST}.create_hover"))
                .c(RAction.suggest_command, f"{current_prefix} {GROUP} {CREATE} ")
            ),
            list_comp.get_page_rtext(page, item_per_page=item_per_page),
            list_comp.get_page_hint_line(
                page,
                item_per_page=item_per_page,
                command_format=f"{current_prefix} {GROUP} {LIST} "
                + self.get_list_command_args_format(),
            ),
        ]
        source.reply(get_rfum_comp_prefix(*text, divider="\n"))

    def info_group_list(self, source: CommandSource, context: CommandContext):
        current_prefix = context.command.split(" ")[0]
        page, item_per_page = self.get_list_args(context)
        group_name = self.get_group_name(context)
        group = self.rfum.group_manager.get_group(group_name)

        if group is None:
            return self.group_not_found(source, group_name)
        if not group.is_src_admin(source):
            return self.perm_denied(source)

        region_list = group.regions

        def get_line(region: Region):
            line = [
                RText("[x]", RColor.red, RStyle.bold)
                .c(
                    RAction.suggest_command,
                    f"{current_prefix} {GROUP} {CONTRACT} {group_name}"
                    + f" {region.x} {region.z} {region.dim}",
                )
                .h(self.ctr("region_list.del_hover")),
                RText(str(region), RColor.aqua),
            ]
            return get_rfum_comp_prefix(*line, divider=" ")

        list_comp = ListComponent(
            region_list, get_line, self.config.default_item_per_page
        )

        text = [
            self.ctr("region_list.title"),
            get_rfum_comp_prefix(
                self.ctr(
                    "region_list.amount", group=group_name, count=len(region_list)
                ),
                RText("[+]", RColor.light_purple, RStyle.bold)
                .h(self.ctr("region_list.add_hover"))
                .c(
                    RAction.suggest_command,
                    f"{current_prefix} {GROUP} {EXPAND} {group_name} ",
                ),
                divider=" ",
            ),
        ]
        page_text = list_comp.get_page_rtext(page, item_per_page=item_per_page)
        if page_text is not None:
            text.append(page_text)
        text += [
            list_comp.get_page_hint_line(
                page,
                item_per_page=item_per_page,
                command_format=f"{current_prefix} {GROUP} {INFO} {group_name} {LIST} "
                + self.get_list_command_args_format(),
            )
        ]
        source.reply(get_rfum_comp_prefix(*text, divider="\n"))

    def create_group(self, source: CommandSource, context: CommandContext):
        group_name = context[NEW_GROUP_NAME]
        if self.is_present(group_name):
            return source.reply(
                get_rfum_comp_prefix(self.ctr("error.already_exists", group_name))
            )
        group = self.rfum.group_manager.create_group(group_name)
        if group is None:
            source.reply(
                get_rfum_comp_prefix(self.ctr("error.unknown").set_color(RColor.red))
            )
        else:
            if source.is_player:
                group.set_permission(get_player_from_src(source), GroupPermission.admin)
            source.reply(get_rfum_comp_prefix(self.ctr("created", group_name)))

    def delete_group(self, source: CommandSource, context: CommandContext):
        group_name = self.get_group_name(context)
        group = self.rfum.group_manager.get_group(group_name)
        if group is None:
            return self.group_not_found(source, group_name)
        if not group.is_src_admin(source):
            return self.perm_denied(source)
        group = self.rfum.group_manager.delete_group(group_name)
        if group is None:
            source.reply(
                get_rfum_comp_prefix(self.ctr("error.unknown").set_color(RColor.red))
            )
        else:
            source.reply(get_rfum_comp_prefix(self.ctr("deleted", group_name)))

    def info_group(self, source: CommandSource, context: CommandContext):
        current_prefix = context.command.split(" ")[0]
        group_name = self.get_group_name(context)
        group = self.rfum.group_manager.get_group(group_name)
        if group is None:
            return self.group_not_found(source, group_name)
        if not group.is_src_admin(source):
            return self.perm_denied(source)
        text = [
            self.ctr("info.title", group_name),
            get_rfum_comp_prefix(
                self.ctr(
                    "info.regions",
                    count=len(group.regions),
                    hint=self.rtr(f"{LIST}.{LIST}_hint.text")
                    .c(
                        RAction.run_command,
                        f"{current_prefix} {GROUP} {INFO} {group_name} {LIST}",
                    )
                    .h(self.rtr(f"{LIST}.{LIST}_hint.hover")),
                )
            ),
            get_rfum_comp_prefix(
                self.ctr(
                    "info.default_perm",
                    group_perm_tr(group.default_permission).set_color(RColor.dark_aqua),
                ),
            ),
            get_rfum_comp_prefix(
                self.ctr("info.detailed_perm")
                .set_color(RColor.light_purple)
                .c(
                    RAction.run_command,
                    f"{current_prefix} {GROUP} {PERM} {group_name} {LIST}",
                )
            ),
        ]
        source.reply(get_rfum_comp_prefix(*text, divider="\n"))

    def __expand_group(self, source: CommandSource, group_name: str, region: Region):
        group = self.rfum.group_manager.get_group(group_name)
        if group is None:
            return self.group_not_found(source, group_name)
        if not group.is_src_admin(source):
            return self.perm_denied(source)
        if region in group.regions:
            return source.reply(
                get_rfum_comp_prefix(
                    self.ctr(
                        "error.region_exists", region=str(region), group=group_name
                    )
                )
            )
        if group.add_region(region):
            source.reply(
                get_rfum_comp_prefix(
                    self.ctr("expanded", region=str(region), group=group_name)
                )
            )
        else:
            source.reply(
                get_rfum_comp_prefix(self.ctr("error.unknown").set_color(RColor.red))
            )

    def __contract_group(self, source: CommandSource, group_name: str, region: Region):
        group = self.rfum.group_manager.get_group(group_name)
        if group is None:
            return self.group_not_found(source, group_name)
        if not group.is_src_admin(source):
            return self.perm_denied(source)
        if region not in group.regions:
            return source.reply(
                get_rfum_comp_prefix(
                    self.ctr(
                        "error.region_not_found", region=str(region), group=group_name
                    )
                )
            )
        if group.remove_region(region):
            source.reply(
                get_rfum_comp_prefix(
                    self.ctr("contracted", region=str(region), group=group_name)
                )
            )
        else:
            source.reply(
                get_rfum_comp_prefix(self.ctr("error.unknown").set_color(RColor.red))
            )

    def expand_group(self, source: CommandSource, context: CommandContext):
        group_name = context[GROUP_NAME]
        self.__expand_group(
            source, group_name, Region(*self.get_ctx_coordinates(context))
        )

    def contract_group(self, source: CommandSource, context: CommandContext):
        group_name = context[GROUP_NAME]
        self.__contract_group(
            source, group_name, Region(*self.get_ctx_coordinates(context))
        )

    def expand_group_by_player_pos(
        self, source: CommandSource, context: CommandContext
    ):
        group_name = context[GROUP_NAME]
        region = self.get_region_from_player(get_player_from_src(source))
        self.__expand_group(source, group_name, region)

    def contract_group_by_player_pos(
        self, source: CommandSource, context: CommandContext
    ):
        group_name = context[GROUP_NAME]
        region = self.get_region_from_player(get_player_from_src(source))
        self.__contract_group(source, group_name, region)

    def __set_player_permission(
        self,
        source: CommandSource,
        group: Group,
        player: str,
        permission: GroupPermission,
    ):
        player_name = PlayerNameString(player)

        if group.set_permission(player, permission):
            source.reply(
                get_rfum_comp_prefix(
                    self.ctr(
                        "set",
                        player=player_name,
                        group=group.name,
                        perm=group_perm_tr(permission).set_color(RColor.yellow),
                    )
                )
            )
        else:
            source.reply(
                get_rfum_comp_prefix(self.ctr("error.unknown").set_color(RColor.red))
            )

    def tell_permission_change_warning(self, source: CommandSource):
        source.reply(
            get_rfum_comp_prefix(
                self.ctr("requires_confirm_1"),
                get_rfum_comp_prefix(
                    self.ctr(
                        "requires_confirm_2",
                        get_duration_text(
                            self.config.region_protection.permission_modify_repeat_wait_time
                        ),
                    )
                ),
                divider="\n",
            )
        )

    def set_player_permission(self, source: CommandSource, context: CommandContext):
        group_name = self.get_group_name(context)
        group = self.rfum.group_manager.get_group(group_name)
        permission: GroupPermission = context[PERM_ENUM]
        target_player = context[PLAYER]
        confirm = context.get(CONFIRM_COUNT, 0) > 0
        self.verbose(f"Confirm flag = {confirm}")
        if group is None:
            return self.group_not_found(source, group_name)
        if not group.is_src_admin(source):
            return self.perm_denied(source)

        def add_job():
            self.tell_permission_change_warning(source)
            self.__player_perm_jobs[target_player] = PlayerPermissionConfirmJob(
                self, self.__scheduler, target_player, permission
            )
            self.__player_perm_jobs[target_player].start()

        requires_confirm = False
        if self.config.get_lost_permission_requires_confirm() and not confirm:
            with group.keep_modify_context():
                group.set_permission(target_player, permission)
                requires_confirm = not group.get_source_permission(source).is_admin

        if requires_confirm:
            job: Optional[PlayerPermissionConfirmJob] = self.__player_perm_jobs.get(
                target_player
            )
            if job is None:
                return add_job()
            with job.lock:
                if not job.is_running:
                    return add_job()
                if permission is not job.permission:
                    self.tell_permission_change_warning(source)
                    job.modify_permission(permission)
                else:
                    job.stop()
                    del self.__player_perm_jobs[target_player]
                    self.__set_player_permission(
                        source, group, target_player, permission
                    )
            return
        self.__set_player_permission(source, group, target_player, permission)

    def list_player_permission(self, source: CommandSource, context: CommandContext):
        page, item_per_page = self.get_list_args(context)
        group_name = self.get_group_name(context)
        group = self.rfum.group_manager.get_group(group_name)
        current_prefix = context.command.split(" ")[0]
        if group is None:
            return self.group_not_found(source, group_name)
        if not group.is_src_admin(source):
            return self.perm_denied(source)

        def get_player_command(player_tuple: Tuple[str, GroupPermission]):
            player, permission = player_tuple
            line_text = [
                RText("[✎]", RColor.dark_green)
                .c(
                    RAction.suggest_command,
                    f"{current_prefix} {GROUP} {PERM} {group_name} {SET} {player} ",
                )
                .h(
                    self.ctr(
                        "perm_list.edit_hover",
                        player=PlayerNameString(player),
                        group=group_name,
                    )
                ),
                RText("[x]", RColor.red)
                .c(
                    RAction.suggest_command,
                    f"{current_prefix} {GROUP} {PERM} {group_name} {DEL} {player}",
                )
                .h(
                    self.ctr(
                        "perm_list.del_hover",
                        player=PlayerNameString(player),
                        group=group_name,
                    )
                ),
                RText(player, RColor.aqua) + ":",
                group_perm_tr(permission).set_color(RColor.gold),
            ]
            return get_rfum_comp_prefix(*line_text, divider=" ")

        list_comp = ListComponent(
            group.permission_mapping.items(),
            get_player_command,
            self.config.default_item_per_page,
        )
        text = [
            self.ctr("perm_list.title"),
            get_rfum_comp_prefix(
                self.ctr(
                    "perm_list.amount",
                    group=group_name,
                    count=len(group.permission_mapping),
                )
            ),
            list_comp.get_page_rtext(page, item_per_page=item_per_page),
            list_comp.get_page_hint_line(page, item_per_page=item_per_page),
        ]
        source.reply(get_rfum_comp_prefix(*text, divider="\n"))

    def __set_default_permission(
        self, source: CommandSource, group: Group, permission: GroupPermission
    ):
        if group.set_default_permission(permission):
            source.reply(
                get_rfum_comp_prefix(
                    self.ctr(
                        "set_default_perm",
                        group=group.name,
                        perm=group_perm_tr(permission).set_color(RColor.yellow),
                    )
                )
            )
        else:
            source.reply(
                get_rfum_comp_prefix(self.ctr("error.unknown").set_color(RColor.red))
            )

    def set_default_permission(self, source: CommandSource, context: CommandContext):
        group_name = self.get_group_name(context)
        group = self.rfum.group_manager.get_group(group_name)
        permission: GroupPermission = context[PERM_ENUM]
        confirm = self.get_ctx_flag(context, CONFIRM_COUNT)
        if group is None:
            return self.group_not_found(source, group_name)
        if not group.is_src_admin(source):
            return self.perm_denied(source)

        def add_job():
            if not isinstance(source, PlayerCommandSource):
                raise TypeError("Not a PlayerCommandSource")
            self.tell_permission_change_warning(source)
            self.__default_perm_jobs[source.player] = DefaultPermissionConfirmJob(
                self, self.__scheduler, source, permission
            )
            self.__default_perm_jobs[source.player].start()

        requires_confirm = False
        if self.config.get_lost_permission_requires_confirm() and not confirm:
            with group.keep_modify_context():
                group.set_default_permission(permission)
                requires_confirm = not group.get_source_permission(source).is_admin

        if requires_confirm:
            job: Optional[DefaultPermissionConfirmJob] = self.__default_perm_jobs.get(
                get_player_from_src(source)
            )
            if job is None:
                return add_job()
            with job.lock:
                if not job.is_running:
                    return add_job()
                if permission is not job.permission:
                    self.tell_permission_change_warning(source)
                    return job.modify_permission(permission)
                else:
                    job.stop()
                    del self.__default_perm_jobs[get_player_from_src(source)]
                    return self.__set_default_permission(source, group, permission)
        self.__set_default_permission(source, group, permission)

    def __delete_permission(self, source: CommandSource, group: Group, player: str):
        player_name = PlayerNameString(player)

        if group.remove_permission(player):
            source.reply(
                get_rfum_comp_prefix(
                    self.ctr(
                        "deleted_perm",
                        player=player_name,
                        group=group.name,
                    )
                )
            )
        else:
            source.reply(
                get_rfum_comp_prefix(self.ctr("error.unknown").set_color(RColor.red))
            )

    def delete_permission(self, source: CommandSource, context: CommandContext):
        group_name = self.get_group_name(context)
        group = self.rfum.group_manager.get_group(group_name)
        target_player = context[PLAYER]
        confirm = context.get(CONFIRM_COUNT, 0) > 0
        if group is None:
            return self.group_not_found(source, group_name)
        if not group.is_src_admin(source):
            return self.perm_denied(source)

        if (
            target_player
            not in group.get_data(self.rfum.group_manager).player_permission.keys()
        ):
            return source.reply(
                get_rfum_comp_prefix(
                    self.ctr(
                        "error.perm_not_found", PlayerNameString(target_player)
                    ).set_color(RColor.red)
                )
            )

        def add_job():
            self.tell_permission_change_warning(source)
            self.__del_perm_jobs[get_player_from_src(source)] = (
                DeletePermissionConfirmJob(
                    self, self.__scheduler, get_player_from_src(source)
                )
            )
            self.__del_perm_jobs[get_player_from_src(source)].start()

        self.verbose("Collecting requires_confirm flag")
        requires_confirm = False
        if self.config.get_lost_permission_requires_confirm() and not confirm:
            with group.keep_modify_context():
                group.remove_permission(target_player)
                requires_confirm = not group.get_source_permission(source).is_admin
        self.verbose(f"requires_confirm = {requires_confirm}")

        if requires_confirm:
            job: Optional[DeletePermissionConfirmJob] = self.__del_perm_jobs.get(
                get_player_from_src(source)
            )
            if job is None:
                return add_job()
            with job.lock:
                if not job.is_running:
                    return add_job()
                else:
                    job.stop()
                    del self.__default_perm_jobs[get_player_from_src(source)]
        self.__delete_permission(source, group, target_player)

    def scheduler_stop(self):
        if self.__scheduler.running:
            self.__scheduler.remove_all_jobs()
            self.__scheduler.shutdown()
            self.__player_perm_jobs.clear()
            self.verbose("Group command scheduler stopped")

    def register_event_listeners(self) -> Any:
        self.server.register_event_listener(
            MCDRPluginEvents.PLUGIN_UNLOADED,
            lambda *args, **kwargs: self.scheduler_stop(),
        )
