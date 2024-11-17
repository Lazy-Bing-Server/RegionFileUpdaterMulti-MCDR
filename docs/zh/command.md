[English](../command.md) | **中文**

# 指令

默认的指令前缀: `!!rfum` or `!!region` (配置里可以改)

下列指令均已忽略前缀，实际执行的时候别忘了添加一个

Actually almost all the steps can be performed by click, all you need to do is just checking command help in game and clicking

实际上所有步骤都可以用点击来完成，使用的时候，在帮助信息里点来点去就行了

## 通用参数

所有的 `list` 指令节点都支持以下`[页面参数]`:

- `--page <页码>` 选择页码
- `--per-page <项目数>` 选择每页数量


## 指令用法

1. `reload`

    重载 RFUMulti 插件 (更新列表也会被清空)

2. `help <指令>`

    游戏内查询所有指令用法

    此处可填的 `<command>` 值有: `upstream`, `add`, `del`, `del-all`, `list`, `history`, `abort`, `confirm`, `update`, `group`

3. `upstream`

    查询或切换目标上游
    - `upstream` 查询当前上游
    - `upstream list [页面参数]` 查询所有已配置的上游
    - `upstream set <上游名称>` 切换上游

4. `add`

    添加区域或者组至更新列表
    - `add group <组名称>` 添加指定的组
    - 直接 `add` 添加当前区域 (仅限玩家，需要 Minecraft Data API 方可执行)
    - `add <x> <z> <维度>` 添加指定区域

    添加已在别的组中的区域可能受到警告或者限制，取决于组的策略

    所有的 `add` 指令都接受如下参数:
    - `--suppress-warning` 暂时忽略更新警告

5. `del`

    自更新列表删除区域或组
    - `del group <组名称>` 自列表删除一个组
    - 直接 `del` 添加当前区域 (仅限玩家，需要 Minecraft Data API 方可执行)
    - `del <x> <z> <维度>` 删除指定区域

6. `del-all`

    清除更新列表里面所有的区域

7. `list [页面参数]`

    查询当前的更新列表

8. `update`

    执行更新从左, 更新已在更新列表中的所有区域

    该指令接受三个参数:
    - `--instantly` 直接执行更新，无须确认
    - `--requires-confirm` 等待确认，再执行更新
    - `--confirm-time-wait <时长>` 设定确认等待时间，超时将撤销本次执行

    时长格式:
    - `1ms` 1 毫秒
    - `1s` / `1sec` 1 秒
    - `1m` / `1min` 1 分钟
    - `1h` / `1hour` 1 小时
    - `1d` / `1day` 1 天
    - `1mon` / `1month` 1 月
    - `1y` / `1year` 1 年

9. `confirm` / `abort`

    确认或取消等待确认的更新操作

10. `history`

    查询上次更新时间，区域与状态

11. `group`

    建立区域组，集中更新、管理和保护

    使用 `add` / `del` 指令以直接在更新列表中增删该组中包含的全部区域

    基本管理指令:
    - `group create <新组名称>` 创建组
    - `group delete <组名称>` 删除组
    - `group list [页面参数]` 列出所有组
    - `group info <组名称>` 查询一个组的详细信息
    - `group info <组名称> list [页面参数]` 列出组中的区域
    - `group expand <组名称>` 添加当前区域到组中 (仅限玩家，需要 Minecraft Data API 方可执行)
    - `group contract <组名称>` 自该组移除当前区域 (仅限玩家，需要 Minecraft Data API 方可执行)
    - `group expand <组名称> <x> <z> <维度>` 添加指定区域至该组
    - `group contract <组名称> <x> <z> <维度>` 自该组移除指定区域

    Permission policies commands:
    - `group perm[ission] <组名称> list [页面参数]` 列出该组设定的玩家权限
    - `group perm[ission] <组名称> set <player> <权限>` 修改玩家在该组的权限
    - `group perm[ission] <组名称> set-default <权限>` 设定该组中未设定权限的玩家的默认权限
    - `group perm[ission] <组名称> del <玩家>` 自组中删除设定的玩家权限

    若一次权限变更会剥夺执行者自己的管理权限，该指令会被要求再次执行以免误操作

    亦可添加 `--confirm` 指令直接强制执行，无须重复

12. `debug`

    > [!WARNING]
    > 如果你连自己在干嘛都不知道，那就别动

    这部分可不是给一般用户准备的，需要在 `experimental` 配置里启用才能用

    确需使用可阅读函数 `region_file_updater_multi.commands.impl.debug_commands.DebugCommands.add_children_for()` 的代码


## 其他文档

[快速上手](quick_start.md)

[配置文件](config.md)
