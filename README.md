# Region File Updater Multi

A plugin to update region files from multiple upstreams (including [PrimeBackup](https://github.com/PrimeBackup/) databases)

Rebuilt version of [RegionFileUpdater](https://github.com/TISUnion/RegionFileUpdater/),
all the functions of original version are ready to use

*Document of this plugin is still on its way*

> [!WARNING]
> **RegionFileUpdaterMulti** is still in **early access** stage, 
>
> Note that **NEVER** risk using experimental stuff in production environment,
> 
> Please point the commit you can reproduce the issue out before submit


# Yes, I'm ready to have a try!

1. Clone this repo
2. Install requirements
```
cd <location of your local repo>
python -m pip install -r requirements.txt
```
3. Pack
```
python -m mcdreforged pack
```
5. Copy generated `.mcdr` plugin archive to your plugin directory and load in MCDR
6. Install any version of [MinecraftDataAPI](https://github.com/MCDReforged/MinecraftDataAPI)
7. Configure `config/region_file_updater_multi/config.yml` in MCDR instance working directory, the set `enable` to `true`
8. Have a try! Help message goes command `!!region|!!rfum`
