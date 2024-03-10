from mcdreforged.api.command import *
from region_file_updater_multi.utils.misc_tools import RFUMInstance
from region_file_updater_multi.utils.units import Duration


class DurationNode(ArgumentNode):
    def parse(self, text: str) -> ParseResult:
        result = QuotableText("##Temp").parse(text)
        text = result.value.strip()
        try:
            duration = Duration(text)
        except (TypeError, ValueError):
            raise IllegalArgument(
                RFUMInstance.get_rfum().rtr('command.error_message.invalid_duration'),
                result.char_read
            )
        except Exception as exc:
            raise IllegalArgument(
                RFUMInstance.get_rfum().rtr('command.error_message.unexpected') + f': {str(exc)}',
                result.char_read
            )
        return ParseResult(duration, result.char_read)
