# Quick start

## Install

### Prepare

Region File Updater Multi is a [MCDReforged](https://mcdreforged.com) plugin, you must install MCDR and initialize a MCDR server before using

More details go to [MCDReforged document](https://docs.mcdreforged.com/en/latest/quick_start.html)

### Install Python requirements

Region File Updater Multi requires a few python libraries to run, they are all listed in the [requirements.txt]((https://github.com/TISUnion/PrimeBackup/blob/master/requirements.txt))

Use command `pip3 install -r requirements.txt`  to install all required Python requirements

### Install Plugin & dependency

Region File Updater Multi requires [MinecraftDataAPI](https://github.com/MCDReforged/MinecraftDataAPI) to run

Just put MinecraftDataAPI and RegionFileUpdaterMulti in MCDReforged plugin directory, install their Python requirements


## Configure

Configure this plugin before loading it, or it will be prevented from loading by itself


1. Configure section `paths` correctly (docs goes [here](config.md#paths))

    - `destdestination_world_directory`: current server world save folder path
    - `upstreams`: the world saves or pb databases you want to update from
    
    if Prime Backup is not installed in current MCDR instance, and you want to user PB upstreams, the following path is required:
    - `pb_plugin_package_path` path to Prime Backup plugin file
    
    if world save directory structure is modified by mods or it has been updated by Mojang, edit:
    - `dimension_mca_files` path to region mca files of each dimensions

> [!WARNING]
> 
> Upstreams should be confirmed to be valid minecraft world save
> 
> RFUMulti barely validate if its paths are available, the world save structure won't be checked
>
> Enabling `remove_file_while_not_found` in `update_operation` section is suggested if you have confirmed all the upstreams.
> 
> Enabling it will make it intuitive. (Reason is explained in [config](config.md#update-operation)). It's disabled by default in order to avoid any accident.

2. Enable the plugin, set item `enabled` to `true`

## Load

Use `!!MCDR reload plugin` command to load it 

Use `!!region` / `!!rfum` (if prefixes is not edited in config, or use your own custom prefix) to check if it's loaded


## Other documents

[Configuration](config.md)

[Command usage](command.md)
