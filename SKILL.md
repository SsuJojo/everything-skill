---
name: everything
description: Use the Everything desktop search app and its CLI on Windows to search the whole local machine for files and folders. Trigger this skill when the user wants to search for files but did not specify an absolute path or relative location, or when the user wants to export Everything search results, build or open EFU file lists, launch Everything with specific search/view options, or control Everything instances/services.
---

# Everything

Use this skill to search the whole local machine for files and folders with Voidtools Everything. When the user does not specify an absolute path or relative location, treat the request as a whole-PC file search and prefer this skill.

## Core capabilities

1. Search the whole local machine for files and folders with Everything.
2. Narrow a search to a path, parent path, direct parent, file-only scope, or folder-only scope.
3. Launch `Everything.exe` with a specific search state, window state, sort order, or result focus.
4. Export search results to CSV, EFU, TXT, M3U, or M3U8.
5. Build and open EFU file lists.
6. Translate copied Everything documentation or vague user intent into a valid command.

## Trigger rule

Use this skill when the user is trying to find a file or folder but does **not** provide an absolute path or relative location.

Examples that should trigger this skill:

- `帮我找一下 resume.pdf`
- `搜一下电脑里有没有 Cursor 安装包`
- `查找所有 mp3`
- `把最近修改的 20 个文件列出来`
- `只看文件夹`

Do **not** treat it as a whole-PC search if the user already gave a concrete scope such as:

- a full path like `C:\Users\...`
- an explicit relative location like `在项目根目录下找`
- a clear fixed folder like `去下载目录找`

## Workflow

Follow these steps:

1. Decide whether the request is a whole-PC search, scoped search, app-control task, or file-list task.
2. If the user did not specify a path, assume whole-PC search.
3. Choose `es.exe` for command-line search/export work against a running Everything instance.
4. Choose `Everything.exe` for app launch, window control, database actions, service actions, or file-list operations.
5. Normalize vague requests into an exact command before executing.
6. Return the found files, folders, or command result in concise natural language unless the user asked for raw output.

## Quick start

- Prefer `Everything.exe` options when the task is about launching, configuring, indexing, opening windows, or building file lists.
- Prefer `es.exe` when the task is about command-line searching/exporting results from an already running Everything instance.
- If the request came from copied docs or rough option names, normalize them to a real command before executing.
- For destructive or system-level actions such as install, uninstall, service changes, or USN journal operations, ask first unless the user explicitly requested execution.

## Capability map

### 1. Search with `es.exe`

Use `es.exe` for scriptable searches and exports.

Common patterns:

```powershell
es.exe foo
es.exe -regex "^test.*\.js$"
es.exe -sort size -n 20
es.exe -sort dm -n 10
es.exe *.mp3 -export-efu mp3.efu
```

Key switches:

- matching: `-regex`, `-case`, `-whole-word`, `-match-path`
- paging: `-offset <n>`, `-max-results <n>`, `-pause`
- columns/output: `-size`, `-dm`, `-csv`, `-efu`, `-txt`, `-m3u`, `-m3u8`
- export: `-export-csv`, `-export-efu`, `-export-txt`, `-export-m3u`, `-export-m3u8`
- scope: `-path`, `-parent-path`, `-parent`, `/ad`, `/a-d`, `/a[attributes]`
- sorting: `-sort <field>`, `-sort-ascending`, `-sort-descending`, `/oN`, `/o-S`, etc.

Read `references/es-cli.md` when you need more exact flags or examples.

### 2. Launch/control `Everything.exe`

Use `Everything.exe` options when the user wants to open Everything in a specific state, connect to ETP, manage windows, or operate on the database.

Common patterns:

```powershell
Everything.exe -search "ABC|123"
Everything.exe -path "D:\Projects" -sort path
Everything.exe -newwindow -ontop
Everything.exe -toggle-window
Everything.exe -reindex
Everything.exe -db "custom.db" -read-only
```

Main areas:

- search state: `-search`, `-regex`, `-case`, `-wholeword`, `-filter`, `-bookmark`
- results/view: `-sort`, `-details`, `-thumbnails`, `-focus-top-result`, `-select <filename>`
- app/window: `-startup`, `-newwindow`, `-toggle-window`, `-close`, `-maximized`, `-minimized`, `-ontop`
- database: `-db`, `-read-only`, `-reindex`, `-update`, `-nodb`
- service/instance: `-instance`, `-service-port`, `-start-service`, `-stop-service`, `-exit`

Read `references/everything-options.md` when you need the wider `Everything.exe` option set.

### 3. Build or use EFU file lists

Use EFU operations when the user wants a portable index of a folder tree or wants Everything to search a specific saved file list.

Examples:

```powershell
Everything.exe -create-file-list "music.efu" "D:\Music" -create-file-list-include-only "*.mp3;*.flac"
Everything.exe -filelist "C:\lists\music.efu"
Everything.exe -edit "C:\lists\music.efu"
```

### 4. Translate docs into concrete commands

If the user gives a goal like “只搜文件夹” or “按修改时间倒序前 20 个”, map it to a real command.

Examples:

- only folders under a path → `es.exe -path "C:\target" /ad`
- top 20 newest files → `es.exe -sort dm -n 20`
- search in a specific parent only → `es.exe -parent "C:\target" keyword`
- open Everything with prefilled search → `Everything.exe -search "keyword"`

## Decision rule

- Need machine-readable result list or export from an active Everything database → use `es.exe`.
- Need to change app state, windows, services, installation, or database behavior → use `Everything.exe`.
- Need exact switch syntax → read the relevant reference file instead of guessing.

## Safety notes

- Confirm before running install/uninstall, service install/remove, startup registration, URL protocol association, or USN journal changes.
- Confirm target paths before mass file-list creation if the scope is large or ambiguous.
- If Everything is required but not running, say so and start it only if the user asked.

## References

- `references/es-cli.md` — `es.exe` command-line interface summary
- `references/everything-options.md` — `Everything.exe` command-line options summary
