[English](../quick_start.md) | **中文**

# 快速上手

## 安装插件

### 准备工作

Region File Updater Multi (RFUMulti) 是一个 [MCDReforged](https://mcdreforged.com/zh-CN/) 插件, 使用前需要安装好 MCDR 并初始化一个 MCDR 服务器

详情见 [MCDReforged 文档](https://docs.mcdreforged.com/en/latest/quick_start.html)

### 安装 Python 依赖

Region File Updater Multi 需要安装一些 Python 库以来, 已在 [requirements.txt]((https://github.com/TISUnion/PrimeBackup/blob/master/requirements.txt)) 中列出

使用指令 `pip3 install -r requirements.txt` 安装所有依赖

### 安装插件和 MCDR 依赖

RFUMulti 依赖 [MinecraftDataAPI](https://github.com/MCDReforged/MinecraftDataAPI) （可选）

将 MinecraftDataAPI 和 RFUMulti 放到 MCDR 插件目录中，安装好它们的 Python 依赖

启动 MCDR，使用 `!!MCDR r plg` 指令加载插件，此时 RFUMulti 会生成配置文件，然后被卸载


## 配置插件

须在使用前配置好该插件，否则插件会被禁止加载

RFUMulti 配置文件路径: `config/region_file_updater_multi/config.yml`

1. 正确配置 `paths` 部分 (详情见[此处](config.md#paths))

    - `destdestination_world_directory`: 当前存档文件夹路径
    - `upstreams`: 需要自其更新的 Prime Backup 数据库或存档目录
    
    若当前 MCDR 实例未安装 Prime Backup (>=1.7.0), 且需要使用 PB 上游, 则下列路径需要填写:
    - `pb_plugin_package_path` Prime Backup 插件包文件的路径
    
    若需要更新的存档结构与原版有异，或 Mojang 在新版本中更新了结构，则下列路径格式需要修改:
    - `dimension_mca_files` 各 MCA 文件的路径格式

> [!WARNING]
> 
> 应确认好上游配置均指向有效 Minecraft 存档
> 
> RFUMulti 只会检查路径是否存在, 存档结构不会仔细检查
>
> 如上游均已确认有效，建议启用 `update_operation` 部分配置中的 `remove_file_while_not_found`
> 
> 启用该项可以让更新操作更符合直觉 (原因在 [配置文档](config.md#update-operation) 中已解释)，该项默认为禁用以避免事故

2. 启用该插件, 设置项目 `enabled` 为 `true`

## 加载插件

再次使用 `!!MCDR r plg` 指令加载

使用指令 `!!region` / `!!rfum` (若插件前缀未变更, 否则改用配置的自定义前缀) 检查是否已加载


## 其他文档

[配置文件](config.md)

[指令用法](command.md)
