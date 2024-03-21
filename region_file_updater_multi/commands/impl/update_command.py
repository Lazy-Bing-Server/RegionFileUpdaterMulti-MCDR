from mcdreforged.api.all import *

from region_file_updater_multi.commands.impl.abc.complex_work_command import (
    ComplexWorkCommand,
)
from region_file_updater_multi.commands.tree_constants import *
from region_file_updater_multi.components.misc import (
    get_rfum_comp_prefix,
    get_duration_text,
)
from region_file_updater_multi.mcdr_globals import *
from region_file_updater_multi.utils.units import Duration


class UpdateCommand(ComplexWorkCommand):
    @property
    def is_debug_command(self):
        return False

    def add_children_for(self, root_node: AbstractNode):
        def attach_update_arguments(node: Literal):
            node.then(CountingLiteral(INSTANTLY, INSTANTLY_COUNT).redirects(node))
            node.then(
                CountingLiteral(REQUIRES_CONFIRM, REQUIRES_CONFIRM_COUNT).redirects(
                    node
                )
            )
            node.then(
                Literal(CONFIRM_TIME_WAIT).then(self.duration(DURATION).redirects(node))
            )
            return node.requires(
                lambda src, ctx: not (
                    self.get_ctx_flag(ctx, INSTANTLY_COUNT)
                    and self.get_ctx_flag(ctx, REQUIRES_CONFIRM_COUNT)
                ),
                lambda: self.rtr("error_message.exclusive_flags"),
            )

        builder = SimpleCommandBuilder()
        builder.command(UPDATE, self.execute_update)
        builder.literal(UPDATE, self.permed_literal).post_process(
            attach_update_arguments
        )

        # Confirm
        builder.command(CONFIRM, self.confirm_update)
        builder.literal(CONFIRM, self.permed_literal)

        # Abort
        builder.command(ABORT, self.abort_update)
        builder.literal(ABORT, self.permed_literal)
        builder.add_children_for(root_node)

    @property
    def tr_key_prefix(self):
        return TRANSLATION_KEY_PREFIX + f"command.{UPDATE}."

    def execute_update(self, source: CommandSource, context: CommandContext):
        if len(self.rfum.current_session.get_current_regions()) == 0:
            return source.reply(
                get_rfum_comp_prefix(
                    self.ctr("error.list_empty").set_color(RColor.red)
                )
            )
        if self.rfum.current_session.is_session_running:
            return source.reply(
                get_rfum_comp_prefix(
                    self.rtr("error_message.session_running").set_color(RColor.red)
                )
            )
        instantly = self.get_ctx_flag(context, INSTANTLY_COUNT)
        requires_confirm = self.get_ctx_flag(context, REQUIRES_CONFIRM_COUNT)
        time_wait: Duration = context.get(
            DURATION, self.config.update_operation.confirm_time_wait
        )
        current_prefix = context.command.split(" ")[0]

        session = self.rfum.current_session
        regions = session.get_current_regions()
        self.rfum.verbose(
            f"Context: instantly={instantly} requires_confirm={requires_confirm}, time_wait={time_wait}"
        )

        if (
            not requires_confirm
            and self.config.update_operation.update_requires_confirm
        ):
            requires_confirm = True
        if instantly:
            requires_confirm = False

        if len(regions) == 0:
            raise ValueError("No region was selected")
        if instantly and requires_confirm:
            raise ValueError(
                "Multiple mutually exclusive flags found: {INSTANTLY}, {REQUIRES_CONFIRM}"
            )
        if instantly or not self.config.update_operation.update_requires_confirm:
            self.rfum.verbose("Update task started without confirm")
            session.run_session(
                source, requires_confirm=requires_confirm, confirm_time_wait=time_wait
            )
            return

        text = [
            self.rtr(
                f"{UPDATE}.broadcast",
                len(regions),
                self.rtr(f"{UPDATE}.list.text")
                .c(RAction.run_command, f"{current_prefix} {LIST}")
                .h(self.rtr(f"{UPDATE}.list.hover")),
            ),
            self.rtr(
                f"{UPDATE}.make_decision", duration=get_duration_text(int(time_wait.value))
            ),
            self.rtr(f"{UPDATE}.{CONFIRM}_hint.text")
            .c(RAction.run_command, f"{current_prefix} {CONFIRM}")
            .h(self.rtr(f"{UPDATE}.{CONFIRM}_hint.hover"))
            + " "
            + self.rtr(f"{UPDATE}.{ABORT}_hint.text")
            .c(RAction.run_command, f"{current_prefix} {ABORT}")
            .h(self.rtr(f"{UPDATE}.{ABORT}_hint.hover")),
        ]
        self.server.broadcast(
            RTextBase.join("\n", [get_rfum_comp_prefix(item) for item in text])
        )
        session.run_session(
            source, requires_confirm=requires_confirm, confirm_time_wait=time_wait
        )

    # !!rfum confirm
    def confirm_update(self, source: CommandSource):
        if not self.rfum.current_session.is_session_running:
            return source.reply(
                get_rfum_comp_prefix(
                    self.ctr("error.nothing_to_confirm").set_color(RColor.red)
                )
            )
        source.reply(get_rfum_comp_prefix(self.ctr("execute_confirm")))
        self.rfum.current_session.confirm_session()

    # !!rfum abort
    def abort_update(self, source: CommandSource):
        if not self.rfum.current_session.is_session_running:
            return source.reply(
                get_rfum_comp_prefix(
                    self.ctr("error.nothing_to_abort").set_color(RColor.red)
                )
            )
        source.reply(get_rfum_comp_prefix(self.ctr("execute_abort")))
        self.rfum.current_session.abort_session()
