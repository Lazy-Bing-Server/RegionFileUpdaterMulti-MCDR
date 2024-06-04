[English(英文)](README.md) | **中文**

# Region File Updater Multi

一个用于自多个上游（包括 [PrimeBackup](https://github.com/PrimeBackup/) 数据库在内）更新区域文件的插件

实质上是 [RegionFileUpdater](https://github.com/TISUnion/RegionFileUpdater/) 的狗尾续貂，使用体验大同小异

> [!WARNING]
> **RegionFileUpdaterMulti** 会修改当前服务端存档
>
> 请谨记，更新操作将**覆写**当前的区域文件，且该操作不可撤销！
> 
> 更新前勿忘检查更新区域列表，并妥善备份


## 特性

- 支持自 [PrimeBackup](https://github.com/PrimeBackup/) 库更新
- 可配置多个上游，在游戏内切换
- 更安全的操作，过程中出错时文件操作会被还原
- 建立区域组，可一次性成组更新区域
- 组内独立权限系统，可保护组内的区域


## 依赖

[MCDReforged](https://github.com/Fallen-Breath/MCDReforged) `>=2.12.0`

[MinecraftDataAPI](https://github.com/MCDReforged/MinecraftDataAPI) 的任意版本

Python 模块需求请阅 [requirements.txt](requirements.txt)，使用指令 `pip install -r requirements.txt` 直接安装

## 文档

懒得烤了，欢迎PR

[快速上手（英文）](docs/quick_start.md)

[配置文件（英文）](docs/config.md)

[指令用法（英文）](docs/command.md)

## 鸣谢

[世界上第一好用的狐狸姐姐](https://github.com/Fallen-Breath)的 [RegionFileUpdater](https://github.com/TISUnion/RegionFileUpdater) 和 [PrimeBackup](https://github.com/TISUnion/PrimeBackup)

（大雾