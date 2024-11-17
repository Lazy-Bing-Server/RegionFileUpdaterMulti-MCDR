x[English](../config.md) | **中文**

# 配置

RFUMulti 配置文件路径: `config/region_file_updater_multi/config.yml`


## 综合配置
- `enabled`

    类型: `bool`
    
    总开关，设置为 `true` 启用本插件


- `load_custom_translation`

    类型: `bool`
    
    允许加载自定义语言文件
    
    启用后可放置文件名形如 `en_us.yml`, `ja_jp.yml` 或 `zh_cn.yml` 的文件于文件夹 `config/region_file_updater_multi/lang` 中以加载
    
    翻译键可在该仓库的 `lang` 目录中找到

    > [!IMPORTANT]
    > **仅有 `region_file_updater` 打头的键名可被加载以避免影响别的插件**


- `default_item_per_page`

    类型: `int`
    
    如 `!!region list` 或者 `!!region group list` 的游戏内列表界面的默认每页项目数量


## 指令配置

管理 RFUMulti 的指令执行

- `command_prefix`

    类型: `Union[List[str], str]`
    
    该插件的指令前缀, 允许填写多个值


- `permission`

    各键值的类型: `int`
    
    各指令 MCDR 指令的权限要求


## 更新操作配置

包含一系列更新操作中的设置

- `update_requires_confirm`

    类型: `bool`
    
    值为 `false` 时, 执行 `!!region update` 将立即启动更新倒计时
    
    否则, 该更新操作需要得到指令 `!!region confirm` 确认后方会继续执行

- `confirm_time_wait`

    类型: `Duration` (like `10s`, `2min`, `1h`, :> useful fallen)
    
    最大确认等待时长, 若超时更新操作将中止

- `update_delay`

    类型: `Duration`
    
    更新操作会延迟配置的时间后执行, 用户仍可在倒计时窗口中使用指令 `!!region abort` 打断更新操作

- `prime_backup_file_not_found_log_format`

    Type: `List[str]`

    RFUMulti 目前通过检查 Prime Backup 标准输出的日志来确定提供的数据库中的备份是否包含指定文件
    
    可调整该配置以适配不同版本的 PB 日志（如有更新的话）

- `remove_file_while_not_found`

    类型: `bool`

    当上游找不到指定文件时, 移除当前存档原有的同名文件
    
    为保证数据安全, 该值默认为 `false`
    
    建议设定为 `true`，因为删除并重生成该区域文件才是更新未生成区域的预期行为
    
    设定为 `true` 之前, 请确认您的上游配置有效且包含结构正确的存档

## 路径

包含插件相关的路径配置

- `pb_plugin_package_path`

    类型: `Optional[str]`

    若当前 MCDR 实例已安装 PB，留空即可

    否则需要设置一个有效的 PB 插件包路径用以自 PB 数据库中提取文件
    
    需要 Prime Backup 版本不小于 1.7

- `destination_world_directory`

    类型: `str`

    设置需要更新的目标存档路径

- `upstream`

    设置需要自其中更新的源世界存档或数据库
    
    是一个允许添加多个可在游戏内切换的上游的 `dict`
    
    键名：该上游的名称
    
    值: 包含三个配置项的字典
    
        # 上游类型
        type: world   # 填写 world 或者 prime_backup
        
        # 上游路径
        对于 Prime Backup, 提供 prime_backup.db 的路径即可
        对于世界存档, 提供存档目录的上一级目录
        path: ../survival/qb_multi/slot1
    
        # 存档文件夹名称
        # 就是将存档文件夹分出来用以兼容 PB 和 QB
        world_name： world


- `dimension_mca_files`

    按维度设置在存档目录中的 MCA 文件路径

    是默认包含三个原版维度配置的字典

    可以添加自定义维度的命名空间 ID （如 `your_namespace:your_dim`）以使 RFUMulti 支持

        dimension_mca_files:
            # 以下为原版维度
            # 默认的情况下只要没问题就别动
            # 除非 Mojang 或者 mod 变更了存档结构
            '-1':
              - DIM{dim}/region/r.{x}.{z}.mca
              - DIM{dim}/poi/r.{x}.{z}.mca
              - DIM{dim}/entities/r.{x}.{z}.mca
            '0':
              - region/r.{x}.{z}.mca
              - poi/r.{x}.{z}.mca
              - entities/r.{x}.{z}.mca
            '1':
              - DIM{dim}/region/r.{x}.{z}.mca
              - DIM{dim}/poi/r.{x}.{z}.mca
              - DIM{dim}/entities/r.{x}.{z}.mca
    
            # 下面添加自定义维度
            # 举个例子:
            "your_namespace:your_dim":
            # 就假设该自定义维度的 MCA 文件在这些路径下
            # 实际配置应按实际路径填写
              - DIM-custom-dim/region/r.{x}.{z}.mca
              - DIM-custom-dim/poi/r.{x}.{z}.mca
              - DIM-custom-dim/entities/r.{x}.{z}.mca

## 区域保护

一些区域保护相关设定，实际保护操作都是在游戏内使用指令完成的

- `enable_group_update_permission_check`

    类型: `bool`
    
    区域保护总开关，不启用怎么设置都不会予以保护

- `check_add_groups`

    类型: `bool`
    
    启用后, 要**添加**到更新列表中的区域组中有区域受其他区域的策略限制时，添加操作也会被限制

- `check_del_operations`

    类型: `bool`
    
    启用后, 自更新列表**移除** 受保护的区域会被阻止

- `permission_modify_repeat_wait_time`

    类型: `Duration`
    
    若一次指令操作会剥夺指令执行者的组管理员权限, 该操作需要执行者执行两次以避免误操作
    
    第二次操作应在此处配置的时间内执行，否则操作将超时中止

- `supress_warning`

    类型: `bool`
    
    抑制未启用保护的组中区域被更新时发出的警告信息


## 实验性特性

> [!WARNING]
> 如果你不知道这里改的啥，那就别动

该部分不是给一般用户准备的，默认都是隐藏的

这部分的内容可能会经常变化，故不提供文档

如确需修改该部分配置，直接去看 `region_file_updater_multi.storage.config.Config.Debug` 类的代码

## 其他文档

[快速上手](quick_start.md)

[指令用法](command.md)
