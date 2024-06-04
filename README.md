**English** | [中文(Chinese)](README_zh.md)

# Region File Updater Multi

A plugin to update region files from multiple upstreams (including [PrimeBackup](https://github.com/PrimeBackup/) databases)

It's a rebuilt version of [RegionFileUpdater](https://github.com/TISUnion/RegionFileUpdater/). Experience may almost be the same.

> [!WARNING]
> **RegionFileUpdaterMulti** will modify your world save of current server
>
> Please keep in mind, update operation will **OVERWRITE** your current region files, and this operation can't be undone
> 
> Never forget to check your region list, and back your world save up before updating!!!


## Features

- [PrimeBackup](https://github.com/PrimeBackup/) databases are supported to update from
- Multiple upstream could be configured to switch in game
- More safe update operation, deleted files will be restored if problem occurs
- Group the regions up, and update these regions in group
- Individual permission system for group, which could protect regions in groups 


## Requirements

[MCDReforged](https://github.com/Fallen-Breath/MCDReforged) `>=2.12.0`

Any version of [MinecraftDataAPI](https://github.com/MCDReforged/MinecraftDataAPI)

Python module requirements goes [requirements.txt](requirements.txt), installing them with `pip install -r requirements.txt`

## Documents

[Quick start](docs/quick_start.md)

[Configuration](docs/config.md)

[Command usage](docs/command.md)

## Thanks

[RegionFileUpdater](https://github.com/TISUnion/RegionFileUpdater) and [PrimeBackup](https://github.com/TISUnion/PrimeBackup) by [\hard-working fox Miss Fallen/](https://github.com/Fallen-Breath)

(xD
