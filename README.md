# everything-skill

这是一个 OpenClaw Skill，用于将 **Voidtools Everything** 封装为可调用技能，为 Windows 提供整机范围的文件与文件夹搜索能力。

它适合这样的场景：当用户想在**整台电脑**里查找文件或文件夹，但**没有明确提供具体路径**时，Agent 可以优先使用 Everything 的索引，而不是只在当前目录或某个局部范围内查找。

## 能做什么

- 全机搜索文件或文件夹
- 按名称、扩展名等条件筛选
- 列出最近修改的匹配项
- 只返回文件或只返回目录
- 使用 Everything / `es.exe` 的查询能力
- 导出 Everything 搜索结果

## 安装

将本仓库作为 `everything` Skill 安装：

```text
https://github.com/SsuJojo/everything-skill.git
```

安装后加载仓库中的 `SKILL.md`，并根据其中的初始化说明检查 Everything 与 `es.exe` 是否可用。

## 适用场景

当用户表达的是以下这类意图时，应使用这个 Skill：

- 在这台电脑里找某个文件
- 搜索所有磁盘 / 全机范围
- 全局列出匹配的文件或文件夹
- 通过 Everything 导出搜索结果

当用户已经明确提供了具体范围时，则不应默认扩大成整机搜索，例如：

- 已给出绝对路径
- 已给出相对路径
- 已明确限定某个文件夹或项目目录

## 仓库内容

- `SKILL.md`：主技能说明
- `references/es-cli.md`：`es.exe` 命令行参考
- `references/everything-options.md`：`Everything.exe` 参数参考

## 示例请求

- 帮我找一下 `resume.pdf`
- 搜一下电脑里所有 `.mp3`
- 查找最近修改的 20 个文件
- 只列出文件夹
- 打开 Everything 并搜索 `ABC|123`
- 导出所有 mp3 为 `mp3.efu`

## 运行前提

- Windows
- Voidtools Everything 已安装并建立索引
- 需要命令行搜索时，`es.exe` 应可调用

搜索结果的覆盖范围取决于 Everything 当前索引状态。

安装、服务管理、USN 日志相关操作属于系统级操作，不应在没有明确需要时自动修改。

## 项目状态

**Working Skill / 可实际调用。**

这是一个刻意保持很小的集成项目：核心价值不在重新实现文件索引，而在于把 Everything 已经非常成熟的搜索能力变成 Agent 可以可靠选择和调用的工具边界。
