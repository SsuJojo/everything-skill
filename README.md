# everything

这是一个 OpenClaw Skill，用于将 Voidtools Everything 封装为可调用技能，为 Windows 提供整机范围的文件与文件夹搜索能力。

它适合这样的场景：当用户想在**整台电脑**里查找文件或文件夹，但**没有明确提供具体路径**时，代理应优先使用 Everything 进行搜索，而不是只在当前目录或某个局部范围内查找。

## 安装

非常简单，你只需将以下消息发送给 OpenClaw：

```markdown
# 请安装数你最灵 skill
1. 从 `https://github.com/SsuJojo/everything-skill.git` 克隆仓库到工作目录的 `skills/` 并更名为 `everything`
2. 将其作为 **skill** 加载，删除 .git 文件夹和 README.md
3. 执行 **Initial implementation scope** 中的指令并标记为已配置
```

## 适用场景

当用户表达的是以下这类意图时，应使用这个 skill：

* 在这台电脑里找某个文件
* 搜索所有磁盘 / 全机范围
* 全局列出匹配的文件或文件夹
* 通过 Everything 导出搜索结果

当用户已经明确提供了具体范围时，则**不应**使用整机搜索逻辑，例如：

* 已给出绝对路径
* 已给出相对路径
* 已明确限定某个文件夹或项目目录

## 包含文件

* `SKILL.md`：主技能说明
* `references/es-cli.md`：`es.exe` 命令行参考
* `references/everything-options.md`：`Everything.exe` 参数参考

## 示例请求

* 帮我找一下 `resume.pdf`
* 搜一下电脑里所有 `.mp3`
* 查找最近修改的 20 个文件
* 只列出文件夹
* 打开 Everything 并搜索 `ABC|123`
* 导出所有 mp3 为 `mp3.efu`

## 说明

* `es.exe` 依赖 Everything 已正确安装并处于运行状态
* 搜索结果覆盖范围取决于 Everything 当前建立的索引
* 安装、服务管理、USN 日志相关操作属于敏感操作，应谨慎处理
