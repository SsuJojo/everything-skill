# Everything Skill

An OpenClaw skill for using Voidtools Everything as a whole-PC file and folder search capability on Windows.

## What it does

This skill tells the agent to treat Everything as the default tool for **searching the whole local machine** when the user wants to find files or folders but does **not** specify an absolute path or relative location.

It also covers:

- `es.exe` command-line searching and exporting
- `Everything.exe` launch/search/window options
- EFU file-list creation and opening
- translating Everything docs into executable commands

## Trigger rule

Use this skill when the user is effectively saying:

- find a file somewhere on this PC
- search all drives / whole machine
- list matching files/folders globally
- export search results from Everything

Do not use whole-PC search behavior when the user already provided a concrete scope, such as a full path, project-relative path, or a clearly named folder.

## Included files

- `SKILL.md` — main skill instructions
- `references/es-cli.md` — `es.exe` reference
- `references/everything-options.md` — `Everything.exe` reference

## Example requests

- 帮我找一下 `resume.pdf`
- 搜一下电脑里所有 `.mp3`
- 查找最近修改的 20 个文件
- 只列出文件夹
- 打开 Everything 并搜索 `ABC|123`
- 导出所有 mp3 为 `mp3.efu`

## Notes

- `es.exe` requires Everything to be installed and running.
- Search coverage depends on what Everything has indexed.
- Installation, service, and USN journal actions should be treated as sensitive operations.
