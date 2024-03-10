from mcdreforged.api.rtext import *
from typing import TYPE_CHECKING, Optional, Union, Iterable

from region_file_updater_multi.mcdr_globals import *

if TYPE_CHECKING:
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti


__rfum: Optional['RegionFileUpdaterMulti'] = None


def set_rfum(rfum: "RegionFileUpdaterMulti"):
    global __rfum
    __rfum = rfum


def get_rfum_comp_prefix(*args, divider: MessageText = ''):
    target = RTextBase.join(divider, args) if len(args) > 0 else ''
    return RText(f"[{SELF_PLUGIN_ABBR}]", RColor.dark_purple).h(RText(SELF_PLUGIN_NAME, RColor.dark_purple)) + ' ' + target


def attach_prefix_to_each_lines(lines: Iterable[MessageText]):
    for line in lines:
        yield get_rfum_comp_prefix(line)


# TODO: combine this to units, so this is a temp solution (also a piece of sh*t)
# This is not the same as TISUnion/Seen, it's a new wheel xD
def get_duration_text(value: int):
    value = int(value)
    color_num, color_unit = RColor.dark_aqua, RColor.dark_purple
    if value == 0:
        return RText(0, color_num) + __rfum.rtr(f'units.duration.sec').set_color(color_unit)
    mapping = {
        "year": 60 * 60 * 24 * 365,
        "mon": 60 * 60 * 24 * 30,
        "day": 60 * 60 * 24,
        "hour": 60 * 60,
        "min": 60,
        "sec": 1,
        # ('ms',): 1e-3,
    }
    text, has_value = [], False
    for n, q in mapping.items():
        count = int(value / q)
        value = value % q
        if count == 0 and not has_value:
            continue
        if not has_value:
            has_value = True
        text.append((count, __rfum.rtr(f'units.duration.{n}').set_color(color_unit)))
    text.reverse()
    index = 0
    for c, q in text.copy():
        if c != 0:
            break
        text.pop(index)
        index += 1
    text.reverse()
    return RText.join(' ', [RText(c, color_num) + ' ' + q for c, q in text])
