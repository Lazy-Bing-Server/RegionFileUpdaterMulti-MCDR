**English** | [中文](zh/command.md)

# Command

Command prefixes by default: `!!rfum` or `!!region` (can be modified in config)

All the commands below has omitted the prefixes, remember adding one of the prefixes when executing commands

Actually almost all the steps can be performed by click, all you need to do is just checking command help in game and clicking


## General Arguments

All the `list` command nodes support `[page_args]`:

- `--page <page_num>` Select current page index
- `--per-page <item_count>` Set item count per page


## Command usage

1. `reload`

    Reload RFUMulti plugin (update list will be cleared)

2. `help <command>`

    Query all the command usage in game

    Available `<command>` values: `upstream`, `add`, `del`, `del-all`, `list`, `history`, `abort`, `confirm`, `update`, `group`

3. `upstream`

    Query and switch target upstreams
    - `upstream` Query current upstream
    - `upstream list [page_args]` Query all the configured upstream
    - `upstream set <upstream_name>` Switch upstream

4. `add`

    Add regions or groups to update list
    - `add group <group_name>` Add specified group
    - Barely `add` Add current region (only players can use, requires Minecraft Data API to run)
    - `add <x> <z> <dimension>` Add specified region

    Adding regions in other group may be denied or warned. That depends on group policies

    All these `add` command can attach an argument:
    - `--suppress-warning` Temporarily suppress update warning

5. `del`

    Delete regions or groups from update list
    - `del group <group_name>` Delete specified group
    - Barely `del` Delete current region (only players)
    - `del <x> <z> <dimension>` Delete specified region

6. `del-all`

    Delete all regions from update list

7. `list [page_args]`

    Query current update list

8. `update`

    Execute update operation, update all the regions in the update list

    This command supports 3 arguments:
    - `--instantly` Executing directly without waiting for confirmation
    - `--requires-confirm` Waiting for confirmation, then execute update
    - `--confirm-time-wait <duration>` Set confirmation waiting time, operation will abort after this duration

    Time duration format:
    - `1ms` 1 millisecond
    - `1s` / `1sec` 1 second
    - `1m` / `1min` 1 minute
    - `1h` / `1hour` 1 hour
    - `1d` / `1day` 1 day
    - `1mon` / `1month` 1 month
    - `1y` / `1year` 1 year

9. `confirm` / `abort`

    Confirm or cancel the pending update operation

10. `history`

     Query last update time, regions and status

11. `group`

    Group the regions up, update, manage or protect them together

    Use `add` / `del` command to add all the regions in a group to update list

    Basic manage commands:
    - `group create <new_group_name>` Create a group
    - `group delete <group_name>` Delete a group
    - `group list [page_args]` Query the list of groups
    - `group info <group_name>` Query general information of a group
    - `group info <group_name> list [page_args]` Query regions in group
    - `group expand <group_name>` Add current region to group (players only)
    - `group contract <group_name>` Remove current region from group (players only)
    - `group expand <group_name> <x> <z> <dimension>`Add specified region to group
    - `group contract <group_name> <x> <z> <dimension>` Remove specified region from group

    Permission policies commands:
    - `group perm[ission] <group_name> list [page_args]` List player permission set in this group
    - `group perm[ission] <group_name> set <player> <permssion>` Modify a player permission in this group
    - `group perm[ission] <group_name> set-default <permission>` Set default permission for not-set players in this group
    - `group perm[ission] <group_name> del <player>` Delete player permission from this group

    If a permission modification will deprive your own admin privilege in this group, this command should be called twice in order to avoid any mistakes
    
    You can also add `--confirm` argument to force executing it without repeating it

12. `debug`

    > [!WARNING]
    > If you don't know what you are doing, stop trying to use them

    These commands are not prepared for normal users and must be enabled in `experimental` section of config to use them

    If you really need to use them, just read the codes in `region_file_updater_multi.commands.impl.debug_commands.DebugCommands.add_children_for()`


## Other documents

[Quick start](quick_start.md)

[Configuration](config.md)
