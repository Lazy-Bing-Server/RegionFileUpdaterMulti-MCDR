from mcdreforged.api.all import *
import os


from region_file_updater_multi.commands.sub_command import AbstractSubCommand
from region_file_updater_multi.commands.tree_constants import *
from region_file_updater_multi.mcdr_globals import *
from region_file_updater_multi.region_upstream_manager import Region


class DebugCommands(AbstractSubCommand):
    @property
    def is_complex(self) -> bool:
        return True

    @property
    def is_debug_command(self):
        return True

    def add_children_for(self, root_node: AbstractNode):
        self.verbose("Debug commands enabled")
        builder = SimpleCommandBuilder()
        builder.command(
            f"{DEBUG} {UPSTREAM} extract file <{TARGET_FILE}>", self.debug_extract_file
        )
        builder.command(
            f"{DEBUG} {UPSTREAM} extract region <{X}> <{Z}> <{DIM}>",
            self.debug_extract_region,
        )
        builder.literal(DEBUG, self.permed_literal)

        def get_allow_not_found_node(name: str):
            node = self.quotable_text(name)
            return node.then(
                CountingLiteral(ALLOW_NOT_FOUND, ANF_COUNT).redirects(node)
            ).then(CountingLiteral("--clear", CLEAR_COUNT).redirects(node))

        self.set_builder_coordinate_args(builder, d_f=get_allow_not_found_node)
        builder.arg(TARGET_FILE, get_allow_not_found_node)
        builder.add_children_for(root_node)

    @property
    def tr_key_prefix(self):
        return TRANSLATION_KEY_PREFIX + "command."

    def debug_extract_file(self, source: CommandSource, context: CommandContext):
        with self.rfum.file_utilities:
            allow_not_found = context.get(ANF_COUNT)
            allow_not_found = allow_not_found is not None and allow_not_found > 0
            file_path = context[TARGET_FILE]
            if context.get(CLEAR_COUNT, 0) > 0:  # type: ignore[operator]
                self.rfum.file_utilities.delete(
                    os.path.join(self.rfum.get_data_folder(), DEBUG)
                )
            try:
                self.rfum.region_upstream_manager.get_current_upstream().extract_file(
                    file_path,
                    os.path.join(self.rfum.get_data_folder(), DEBUG_TEMP_FOLDER),
                    allow_not_found=allow_not_found,
                )
            except Exception as exc:
                source.reply(f"Exception: {str(exc)}")
                raise
            else:
                source.reply("success")

    def debug_extract_region(self, source: CommandSource, context: CommandContext):
        with self.rfum.file_utilities:
            allow_not_found = context.get(ANF_COUNT)
            allow_not_found = allow_not_found is not None and allow_not_found > 0
            region = Region(context[X], context[Z], context[DIM])
            if context.get(CLEAR_COUNT, 0) > 0:  # type: ignore[operator]
                self.rfum.file_utilities.delete(
                    os.path.join(self.rfum.get_data_folder(), DEBUG)
                )
            try:
                self.rfum.region_upstream_manager.extract_region_files(
                    region,
                    os.path.join(self.rfum.get_data_folder(), DEBUG_TEMP_FOLDER),
                    allow_not_found=allow_not_found,
                )
            except Exception as exc:
                source.reply(f"Exception: {str(exc)}")
                raise
            else:
                source.reply("success")
