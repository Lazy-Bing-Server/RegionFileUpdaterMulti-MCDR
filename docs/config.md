# Configuration

Region file updater multi config path: `config/region_file_updater_multi/config.yml`


## General settings
- `enabled`

type: `bool`

Set it to true to enable this plugin


- `load_custom_translation`

Type: `bool`

Enable custom translation files loading

Place language files like `en_us.yml`, `ja_jp.yml` or `zh_cn.yml` in folder `config/region_file_updater_multi/lang` to load them

Translation keys could be found in `lang` directory in this repository

> [!IMPORTANT]
> **Only keys starts with `region_file_updater` will be loaded to avoid influencing other plugins**


- `default_item_per_page`

Type: `int`

Default item count per page of in-game list command, such as `!!region list` or `!!region group list`


## Command

Manage command execution of this plugin

- `command_prefix`

Type: `Union[List[str], str]`

Command prefix of this plugin, multiple values allowed


- `permission`

Type of each key: `int`

MCDR permission requirement for each command


## Update Operation

Contains a series of settings during update operations

- `update_requires_confirm`

Type: `bool`

If its value is `false`, executing `!!region update` will start update countdown immediately 

Otherwise, this command execution requires an additional confirmation with command `!!region confirm`

- `confirm_time_wait`

Type: `Duration` (like `10s`, `2min`, `1h`, :> useful fallen)

Maximum confirmation wait time, execution will abort after it expires

- `update_delay`

Type: `Duration`

Update execution will delay and countdown for configured duration, users can still interrupt this execution with command `!!region abort`

- `prime_backup_file_not_found_log_format`

Type: `List[str]`

RFUM now check Prime Backup stdout log to determine whether this file is found in the provided backup of the database

Modify this value to make it compatible with different version of PB logs


## Paths

Contains settings of plugin-related paths

- `pb_plugin_package_path`

Type: `Optional[str]`

Just leave it blank when this MCDR instance have PB installed

Otherwise, you should set a PB plugin path to extract files from PB databases

- `destination_world_directory`

Type: `str`

Set the target world save directory you want to update

- `upstream`

Set the source world save or database you want to update from.

This is a `dict` that allows you to set multiple upstreams and switch in game

Key: the name of this upstream

Value: a dict contains 3 upstream information keys

    # The upstream type
    type: world   # world / prime_backup
    
    # The upstream path
    For Prime Backup databases, provides path to prime_backup.db
    For world saves, provides path to the parent directory of world save folder
    path: ../survival/qb_multi/slot1

    # The world directory name
    # Split the path config to 2 keys to support PB / QB
    world_name： world


- `dimension_region_folder`

Set the dimension-related MCA folder path in world save directory

This is a `dict` that contains folders for 3 dimensions by default

> [!IMPORTANT]
> This item is from [RegionFileUpdater](https://github.com/TISUnion/RegionFileUpdater)
> 
> It's almost the same with the original item, but this is not compatible with the files not named with `r.<x>.<y>.mca`
>
> But I'm lazy, so... :> this item path format **may** be changed in the future to support updating these dimension-related files with irregular names
>
> But when? who knows...(xD)

You can add custom dimension name with its namespace id (like `your_namespace:your_dim`) to make this plugin support them


    dimension_region_folder:
        # These are the vanilla dimensions
        # It's not supposed to change these if plugin works
        # Only change these when these were changed by mods or mojang in new versions
        '-1':
          - DIM-1/region
          - DIM-1/poi
        '0':
          - region
          - poi
        '1':
          - DIM1/region
          - DIM1/poi

        # Add your custom dimensions here
        # For example:
        "your_namespace:your_dim":
        # We assumed the MCA paths of this dim are these here
        # Actual paths should match your own actual situation
          - DIM-custom-dim/region
          - DIM-custom-dim/poi


## Region Protection

Some region permission settings, actual protection operation should be performed in game with commands

- `enable_group_update_permission_check`

Type: `bool`

Group update protection main switch

- `check_add_groups`

Type: `bool`

If enabled, **adding** group to update list while any region in this group is protected by any other group will be prevented

- `check_del_operations`

Type: `bool`

If enabled, **removing** protected regions (and groups if `check_add_groups` enabled) from update list will be prevented

- `permission_modify_repeat_wait_time`

Type: `Duration`

When a command operation will deprive the command executor's administrator privilege, this command will require the executor executing twice to avoid mistakes

The second execution should be operated in the time configured here or the execution will be cancelled

- `supress_warning`

Type: `bool`

Supress the warning when a region in a not protected group being adding to the update list


## Debug

> [!WARNING]
> If you don't know what you are doing, stop trying to edit this section of config

This section is not provided for normal users and it's hided by default

Item here may be changed frequently so documents won't be provided

If you really need to edit these items, just read the codes in class `region_file_updater_multi.storage.config.Config.Debug`
