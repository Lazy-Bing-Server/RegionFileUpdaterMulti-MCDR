"""
    Literal {'!!rfum', '!!region'}
    ├── Literal 'reload'
    ├── Literal 'help'
    │   ├── Literal 'upstream'
    │   ├── Literal {'add', 'del', 'del-all'}
    │   ├── Literal 'list'
    │   ├── Literal 'history'
    │   ├── Literal {'abort', 'confirm', 'update'}
    │   └── Literal 'group'
    ├── Literal 'upstream'
    │   ├── Literal 'list'
    │   │   ├── Literal '--page'
    │   │   │   └── Integer <page_num>
    │   │   └── Literal '--per-page'
    │   │       └── Integer <item_count>
    │   └── Literal 'set'
    │       └── _QuotableText <upstream_name>
    ├── Literal 'add'
    │   ├── Literal '--suppress-warning'
    │   ├── Literal 'group'
    │   │   └── _QuotableText <group_name>
    │   │       └── Literal '--suppress-warning'
    │   └── _Integer <x>
    │       └── _Integer <z>
    │           └── _QuotableText <dimension>
    │               └── Literal '--suppress-warning'
    ├── Literal 'del'
    │   ├── Literal 'group'
    │   │   └── _QuotableText <group_name>
    │   │       └── Literal '--suppress-warning'
    │   └── _Integer <x>
    │       └── _Integer <z>
    │           └── _QuotableText <dimension>
    ├── Literal 'del-all'
    ├── Literal 'list'
    │   ├── Literal '--page'
    │   │   └── Integer <page_num>
    │   └── Literal '--per-page'
    │       └── Integer <item_count>
    ├── Literal 'update'
    │   ├── Literal '--instantly'
    │   ├── Literal '--requires-confirm'
    │   └── Literal '--confirm-time-wait'
    │       └── _DurationNode <duration>
    ├── Literal 'confirm'
    ├── Literal 'abort'
    ├── Literal 'history'
    │   └── Literal 'list'
    │       ├── Literal '--page'
    │       │   └── Integer <page_num>
    │       └── Literal '--per-page'
    │           └── Integer <item_count>
    ├── Literal 'group'
    │   ├── Literal 'expand'
    │   │   └── _QuotableText <group_name>
    │   │       └── _Integer <x>
    │   │           └── _Integer <z>
    │   │               └── _QuotableText <dimension>
    │   ├── Literal 'contract'
    │   │   └── _QuotableText <group_name>
    │   │       └── _Integer <x>
    │   │           └── _Integer <z>
    │   │               └── _QuotableText <dimension>
    │   ├── Literal {'perm', 'permission'}
    │   │   └── _QuotableText <group_name>
    │   │       ├── Literal 'list'
    │   │       │   ├── Literal '--page'
    │   │       │   │   └── Integer <page_num>
    │   │       │   └── Literal '--per-page'
    │   │       │       └── Integer <item_count>
    │   │       ├── Literal 'set'
    │   │       │   └── _QuotableText <player>
    │   │       │       ├── Literal '--confirm'
    │   │       │       └── _Enumeration <permission> (GroupPermission)
    │   │       │           └── Literal '--confirm'
    │   │       ├── Literal 'set-default'
    │   │       │   └── _Enumeration <permission> (GroupPermission)
    │   │       │       └── Literal '--confirm'
    │   │       └── Literal 'del'
    │   │           └── _QuotableText <player>
    │   │               └── Literal '--confirm'
    │   ├── Literal 'list'
    │   │   ├── Literal '--page'
    │   │   │   └── Integer <page_num>
    │   │   └── Literal '--per-page'
    │   │       └── Integer <item_count>
    │   ├── Literal 'create'
    │   │   └── _QuotableText <new_group_name>
    │   ├── Literal 'delete'
    │   │   └── _QuotableText <group_name>
    │   └── Literal 'info'
    │       └── _QuotableText <group_name>
    │           └── Literal 'list'
    │               ├── Literal '--page'
    │               │   └── Integer <page_num>
    │               └── Literal '--per-page'
    │                   └── Integer <item_count>
    └── Literal 'debug'
        ├── Literal 'players'
        └── Literal 'upstream'
            └── Literal 'extract'
                ├── Literal 'file'
                │   └── _QuotableText <target_file>
                │       ├── Literal '--allow-not-found'
                │       └── Literal '--clear'
                └── Literal 'region'
                    └── _Integer <x>
                        └── _Integer <z>
                            └── _QuotableText <dimension>
                                ├── Literal '--allow-not-found'
                                └── Literal '--clear'
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
