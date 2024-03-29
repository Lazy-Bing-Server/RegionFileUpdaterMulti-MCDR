import datetime

from mcdreforged.api.rtext import *
from typing import Union, Iterable, TYPE_CHECKING

from region_file_updater_multi.mcdr_globals import *
from region_file_updater_multi.utils.misc_tools import RFUMInstance
from region_file_updater_multi.utils.units import Duration

if TYPE_CHECKING:
    from region_file_updater_multi.storage.group import GroupPermission


class PlayerNameString(str):
    @property
    def possessive(self):
        if self.endswith("s"):
            return self + "'"
        else:
            return self + "'s"


def get_rfum_comp_prefix(*args, divider: MessageText = ""):
    target = RTextBase.join(divider, args) if len(args) > 0 else ""
    return (
        RText(f"[{SELF_PLUGIN_ABBR}]", RColor.dark_purple).h(
            RText(SELF_PLUGIN_NAME, RColor.dark_purple)
        )
        + " "
        + target
    )


def attach_prefix_to_each_lines(lines: Iterable[MessageText]):
    for line in lines:
        yield get_rfum_comp_prefix(line)


# TODO: combine this to units, so this is a temp solution (also a piece of sh*t)
# This is not the same as TISUnion/Seen, it's a new wheel xD
def get_duration_text(raw_value: Union[int, Duration]):
    if isinstance(raw_value, Duration):
        value = raw_value.value
    else:
        value = int(raw_value)
    rfum = RFUMInstance.get_rfum()
    color_num, color_unit = RColor.dark_aqua, RColor.dark_purple
    if value == 0:
        return RText(0, color_num) + rfum.rtr("units.duration.sec").set_color(
            color_unit
        )
    mapping = {
        "year": 60 * 60 * 24 * 365,
        "mon": 60 * 60 * 24 * 30,
        "day": 60 * 60 * 24,
        "hour": 60 * 60,
        "min": 60,
        "sec": 1,
        # ('ms',): 1e-3,
    }
    text = []
    for n, q in mapping.items():
        count = int(value / q)
        value = value % q
        text.append((count, rfum.rtr(f"units.duration.{n}").set_color(color_unit)))

    text = list(filter(lambda item: item[0] != 0, text))
    return RText.join(" ", [RText(c, color_num) + " " + q for c, q in text])


def datetime_tr(time: Union[int, float, datetime.datetime, None] = None):
    def __tr(translation_key: float, *args, **kwargs):
        target_time = datetime.datetime.fromtimestamp(float(translation_key))
        return target_time.strftime(
            RFUMInstance.get_rfum().ntr(f"{SELF_PLUGIN_ID}.format.datetime")
        )

    if time is None:
        time = datetime.datetime.now()
    if isinstance(time, datetime.datetime):
        time = time.timestamp()
    return RTextMCDRTranslation(str(time)).set_translator(__tr)


def group_perm_tr(key: Union["GroupPermission", str]):
    if not isinstance(key, str):
        key_string = key.name
    else:
        key_string = str(key)
    key_string = f"group_permission.{key_string}"
    return RFUMInstance.get_rfum().rtr(key_string)
