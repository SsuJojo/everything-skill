---
name: everything
description: Search an entire Windows PC for files and folders with Voidtools Everything. Use for machine-wide searches when the user has not supplied a specific directory, especially when bounded results, Unicode paths, or pagination are useful.
---

# Everything

Use this Skill for whole-PC file and folder searches on Windows. If the user already supplied a concrete path or project directory, use the normal filesystem tools for that scope instead.

## Requirements

- Windows
- Python 3.10 or newer
- Everything installed, indexed, and running
- The current execution environment can reach the Everything IPC interface

Being able to read this Skill does not prove that an Agent sandbox can access Everything on the host. IPC may still be isolated.

## Locate runtime files

Treat the directory containing this `SKILL.md` as the Skill root. Resolve runtime files from that directory:

- `scripts/es_wrapper.py` — normal search entrypoint
- `scripts/ensure-everything-tools.ps1` — CLI and IPC diagnostic/repair helper
- `bin/es.exe` — bundled ES command-line client

Do not assume a particular workspace, username, Agent product, or installation path.

## Search workflow

1. Resolve `scripts/es_wrapper.py` from the Skill root.
2. Run the wrapper with `--format json` for ordinary searches.
3. Keep the default result limit unless the user asks for more.
4. For broad searches, request another page with `--offset`.
5. Stop paging after an empty page or a page shorter than the requested limit.
6. Summarize useful matches instead of dumping large result sets.

Conceptual commands, where `<skill-root>` is resolved at runtime:

```powershell
python "<skill-root>\scripts\es_wrapper.py" --format json -- "resume.pdf"
python "<skill-root>\scripts\es_wrapper.py" --format json --output-limit 10 -- "*.mp3"
python "<skill-root>\scripts\es_wrapper.py" --format json --output-limit 10 --offset 10 -- "*.mp3"
python "<skill-root>\scripts\es_wrapper.py" --format json -- /ad "project"
```

The wrapper passes arguments after `--` to ES. It adds `-argv` for Unicode input, locates the bundled executable relative to itself, and injects `-max-results` and `-offset` only when the caller did not already supply them.

The JSON output includes the ES command and return code, decoded result lines, counts, limit metadata, the effective offset, and `next_offset`. This is a convenience response for Agents, not a separate public SDK contract.

For ES output modes such as version, statistics, columns, CSV, or JSON, prefer wrapper text mode so ES stdout remains direct:

```powershell
python "<skill-root>\scripts\es_wrapper.py" --format text -- -get-result-count "*.pdf"
```

## Diagnose or repair ES

Run the helper without download flags to validate the bundled CLI and test real IPC connectivity:

```powershell
pwsh -NoProfile -File "<skill-root>\scripts\ensure-everything-tools.ps1"
```

If ES is missing or incompatible, obtain user consent before allowing a download from the official `voidtools/ES` GitHub release:

```powershell
pwsh -NoProfile -File "<skill-root>\scripts\ensure-everything-tools.ps1" -AllowDownload
```

ES return code `8` means the expected Everything IPC window could not be reached. Possible causes include Everything not being installed or running, a named-instance mismatch, or sandbox isolation. Do not claim that Everything is uninstalled based only on this code.

## Export and state-changing options

ES export arguments are passed through unchanged. Use `--output-limit -1` when a complete export must not receive the wrapper's default ES result limit. Follow the host Agent's normal confirmation rules before writing or overwriting files.

Obtain confirmation before ES or Everything options that change settings, run history, indexes, services, installation state, or files.

## References

- [`references/es-cli.md`](references/es-cli.md) — ES 1.1.0.37 search, output, export, and return-code reference
- [`references/everything-options.md`](references/everything-options.md) — selective `Everything.exe` GUI and administration reference
