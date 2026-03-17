---
name: everything
description: Search the whole Windows PC for files or folders with Voidtools Everything. Use when the user wants to find files/folders but did not give an absolute path or a clear fixed folder. Prefer this skill for broad machine-wide search, especially when Chinese file paths, result limiting, and pagination matter.
---

# Everything

Use this skill for whole-PC file and folder search on Windows.

## Core job

1. Treat requests without a concrete path as whole-PC search.
2. Use `skills\everything\scripts\es_wrapper.py` as the default entrypoint.
3. Let the wrapper call `skills\everything\bin\es.exe`, decode raw bytes safely, and return UTF-8 text or JSON.
4. Keep both search volume and output volume capped by default.
5. Use pagination with `--offset` for broad queries.
6. Use `Everything.exe` only if the task explicitly needs the GUI or `es.exe` cannot solve it.

## Trigger rule

Use this skill when the user wants to find a file or folder but does **not** provide a concrete path scope.

Examples:

- `帮我找一下 resume.pdf`
- `搜一下电脑里有没有 Cursor 安装包`
- `查找所有 mp3`
- `把最近修改的 20 个文件列出来`
- `只看文件夹`

Do **not** use whole-PC search behavior when the user already gave:

- a full path like `C:\Users\...`
- a relative scope like `在项目根目录下找`
- a fixed folder like `去下载目录找`

## Workflow

1. Decide whether the request is a whole-PC search.
2. If the user did not specify a path, search with `es_wrapper.py` first.
3. Keep the wrapper default limits unless the user clearly asks for more results.
4. For large result sets, page with `--offset` instead of dumping more rows at once.
5. If `es.exe` is missing or broken, repair it with `scripts\ensure-everything-tools.ps1` and retry.
6. Use `Everything.exe` only as a fallback for GUI-specific tasks.
7. Return concise natural-language results unless the user asked for raw output.

## Response style for search requests

- Send only one short progress line before searching: `正在使用 Everything 查找…`
- Do not narrate extra internal steps.
- After the progress line, directly return the result.
- If the task is simply “find and send a file”, send it immediately once found.

## Quick start

- Default entrypoint:

```powershell
python skills\everything\scripts\es_wrapper.py -- <query>
```

- Limit rows explicitly when needed:

```powershell
python skills\everything\scripts\es_wrapper.py --output-limit 10 -- <query>
```

- Get the next page:

```powershell
python skills\everything\scripts\es_wrapper.py --output-limit 10 --offset 10 -- <query>
```

## Wrapper behavior

`skills\everything\scripts\es_wrapper.py` should be the normal path for searches.

It should:

- call `skills\everything\bin\es.exe`
- capture stdout/stderr as raw bytes
- decode Chinese paths safely
- emit UTF-8 text or JSON
- cap output by default
- inject `-max-results` when the caller forgot to limit results
- inject `-offset` when using wrapper pagination and the caller did not already set one
- return pagination metadata such as `next_offset`

Use `--output-limit -1` only when the task truly needs unrestricted output.

## Common patterns

```powershell
python skills\everything\scripts\es_wrapper.py -- 晴天
python skills\everything\scripts\es_wrapper.py --output-limit 10 -- 1
python skills\everything\scripts\es_wrapper.py --output-limit 10 --offset 10 -- 1
python skills\everything\scripts\es_wrapper.py --output-limit 20 -- -sort dm -n 20
python skills\everything\scripts\es_wrapper.py --output-limit 20 -- /ad <query>
```

## Fallbacks

### Repair `es.exe`

If `skills\everything\bin\es.exe` is missing or cannot run, use:

- `skills\everything\scripts\ensure-everything-tools.ps1`

### Use `Everything.exe` only when necessary

If the task explicitly requires the GUI app, locate `Everything.exe` first and run it by absolute path.
Do not rely on `PATH`.

## Safety notes

- Do not change the global shell code page just to fix output.
- Do not dump large result sets into context unless the user clearly asked for that.
- Confirm before destructive or system-level actions.

## References

- `references/es-cli.md` — `es.exe` flag reference
- `references/everything-options.md` — `Everything.exe` option reference when GUI fallback is truly needed
