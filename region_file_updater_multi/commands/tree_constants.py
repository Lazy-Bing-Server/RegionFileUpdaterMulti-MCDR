"""
Written by hand before building this tree, not printed by SimpleCommandBuilder.print_tree()
Might be slightly different to the actual tree

    Literal '!!rfum'
    ├── Literal 'upstream'
    │   ├── Literal 'list'
    │   └── Literal 'set'
    │       └── QuotableText <upstream>
    ├── Literal 'add'
    │   └── Integer <x>
    │       └── Integer <z>
    │           └── QuotableText <dimension>
    ├── Literal 'del'
    │   └── Integer <x>
    │       └── Integer <z>
    │           └── QuotableText <dimension>
    ├── Literal 'del-all'
    ├── Literal 'list'
    ├── Literal 'update'
    ├── Literal 'confirm'
    ├── Literal 'abort'
    ├── Literal 'history'
    ├── Literal 'group'
    │   ├── Literal 'list'
    │   ├── Literal 'create'
    │   │   └── QuotableText <new_range>
    │   ├── Literal 'delete'
    │   │   └── QuotableText <range>
    │   ├── Literal 'info'
    │   │   └── QuotableText <range>
    │   ├── Literal 'use'
    │   │   └── QuotableText <range>
    │   ├── Literal 'append'
    │   │   └── QuotableText <range>
    │   │       └── Integer <x>
    │   │           └── Integer <z>
    │   │               └── QuotableText <dimension>
    │   ├── Literal 'contract'
    │   │   └── QuotableText <range>
    │   │       └── Integer <x>
    │   │           └── Integer <z>
    │   │               └── QuotableText <dimension>
    │   ├── Literal 'protect'
    │   │   └── QuotableText <range>
    │   │       ├── Literal 'enable'
    │   │       └── Literal 'disable'
    │   ├── Literal 'whitelist'
    │   │   └── QuotableText <range>
    │   │       ├── Literal 'append'
    │   │       │   └── QuotableText <player_to_be_whitelisted>
    │   │       ├── Literal 'remove'
    │   │       │   └── QuotableText <whitelisted_player>
    │   │       ├── Literal 'enable'
    │   │       └── Literal 'disable'
    │   └── Literal 'blacklist'
    │       └── QuotableText <range>
    │           ├── Literal 'append'
    │           │   └── QuotableText <player_to_be_blacklisted>
    │           ├── Literal 'remove'
    │           │   └── QuotableText <blacklisted_player>
    │           ├── Literal 'enable'
    │           └── Literal 'disable'
    └── Literal 'reload'
"""

# Literals
HELP = "help"
UPSTREAM = "upstream"
ADD = "add"
DEL = "del"
DEL_ALL = "del-all"
LIST = "list"
UPDATE = "update"
CONFIRM = "confirm"
ABORT = "abort"
HISTORY = "history"
GROUP = "group"
USE = "use"
ENABLE = "enable"
DISABLE = "disable"
WHITELIST = "whitelist"
BLACKLIST = "blacklist"
PROTECT = "protect"
RELOAD = "reload"

PERMISSION = "permission"
PERM = "perm"
CREATE = "create"
DELETE = "delete"
INFO = "info"
EXPAND = "expand"
CONTRACT = "contract"

SET = "set"
SET_DEFAULT = "set-default"

# Arguments
UPS_NAME = "upstream_name"
GROUP_NAME = "group_name"
NEW_GROUP_NAME = "new_group_name"
PLAYER = "player"
PERM_ENUM = "permission"

X = "x"
Z = "z"
DIM = "dimension"
PAGE_INDEX = "page_num"
ITEM_PER_PAGE = "item_count"

# Optional
INSTANTLY = "--instantly"
INSTANTLY_COUNT = "instantly_count"
REQUIRES_CONFIRM = "--requires-confirm"
REQUIRES_CONFIRM_COUNT = "requires_confirm_count"
CONFIRM_TIME_WAIT = "--confirm-time-wait"
CONFIRM_FLAG = "--confirm"
CONFIRM_COUNT = "confirm_flag"
SUPRESS_WARNING = "--suppress-warning"
DURATION = "duration"

# Debug
DEBUG = "debug"
TARGET_FILE = "target_file"

ALLOW_NOT_FOUND = "--allow-not-found"
ANF_COUNT = "anf_count"
CLEAR_COUNT = "clear_count"
