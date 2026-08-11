# ES 1.1.0.37 command-line reference

Use ES to query an existing Everything index over IPC. Everything must be running, and the current execution environment must be able to reach its IPC interface.

```text
es.exe [options] [search text]
```

When using the wrapper, place wrapper options before `--` and ES options after it:

```powershell
python "<skill-root>\scripts\es_wrapper.py" --format json --output-limit 10 -- -sort size "*.zip"
```

The wrapper fixes the first ES options to `-argv -cp 65001`. ES 1.1.0.37 uses `-argv` to recover Unicode command-line arguments with `CommandLineToArgvW`; `-cp 65001` makes redirected stdout and stderr UTF-8. Caller-supplied code-page options are replaced by this wrapper setting.

## Search and matching

- `-r <search>`, `-regex <search>` — regular expression search
- `-i`, `-case` — case-sensitive matching
- `-w`, `-ww`, `-whole-word`, `-whole-words` — whole-word matching
- `-p`, `-match-path` — match full paths
- `-a`, `-diacritics` — diacritic-sensitive matching
- `-path <path>` — search descendants of a path
- `-parent-path <path>` — search descendants of a path's parent
- `-parent <path>` — search direct children of a path
- `/ad` — folders only
- `/a-d` — files only
- `/a[attributes]` — DIR-style attribute filter

Everything search syntax uses spaces for AND, `|` for OR, `!` for NOT, and angle brackets to group terms.

## Limits and paging

- `-o <offset>`, `-offset <offset>` — zero-based starting result
- `-n <count>`, `-max-results <count>` — maximum displayed results
- `-get-result-count` — print the total result count
- `-get-total-size` — print the total size of matching results

For normal path searches, prefer the wrapper's `--output-limit` and `--offset`. Continue with the returned `next_offset`; stop after a short or empty page.

## Columns and sorting

Common display columns include:

- `-name`
- `-path-column`
- `-full-path-and-name`, `-filename-column`
- `-extension`, `-ext`
- `-size`
- `-date-created`, `-dc`
- `-date-modified`, `-dm`
- `-date-accessed`, `-da`
- `-attributes`, `-attribs`, `-attrib`
- `-run-count`
- `-date-run`
- `-date-recently-changed`, `-rc`

Use `-sort <field>`, `-sort-<field>`, or append `-ascending`/`-descending`. Common fields include name, path, size, extension, dates, attributes, run-count, and date-run.

DIR-style aliases include `/on`, `/o-n`, `/os`, `/o-s`, `/oe`, `/o-e`, `/od`, and `/o-d`.

## Native stdout formats

- `-csv`
- `-efu`
- `-json`
- `-m3u`
- `-m3u8`
- `-tsv`
- `-txt`

These options change ES stdout. Use wrapper `--format text` when the output is not a simple list of paths; the wrapper deliberately does not interpret every ES output mode.

Formatting options include `-no-header`, `-utf8-bom`, `-double-quote`, `-size-format <0..3>`, and `-date-format <0..3>`.

## File exports

- `-export-csv <out.csv>`
- `-export-efu <out.efu>`
- `-export-json <out.json>`
- `-export-m3u <out.m3u>`
- `-export-m3u8 <out.m3u8>`
- `-export-tsv <out.tsv>`
- `-export-txt <out.txt>`

Export arguments pass through unchanged. Use wrapper `--output-limit -1` for a complete export, and follow the host Agent's normal confirmation rules before writing or overwriting files.

## General and state-changing options

- `-cp <code-page>`, `-code-page <code-page>` — set the console or redirected output code page; 65001 is UTF-8
- `-instance <name>` — connect to a named Everything instance
- `-ipc1`, `-ipc2` — select an older IPC protocol
- `-timeout <milliseconds>` — wait for the Everything database before querying
- `-version` — print the ES version
- `-get-everything-version` — print the Everything version
- `-no-result-error` — return code 9 when there are no results
- `-save-settings`, `-clear-settings` — mutate `es.ini`
- `-set-run-count`, `-inc-run-count` — mutate run history
- `-exit`, `-save-db`, `-reindex` — affect the running Everything instance

Obtain user confirmation before state-changing options.

## Native return codes

| Code | Meaning |
| ---: | --- |
| 0 | Success |
| 1 | Window class registration failed |
| 2 | IPC listener window creation failed |
| 3 | Out of memory |
| 4 | An option is missing a required value |
| 5 | An export file could not be created |
| 6 | Unknown option |
| 7 | IPC query send failed |
| 8 | The Everything IPC window could not be reached |
| 9 | No results when `-no-result-error` is active |

Code `8` can mean Everything is absent or stopped, a named instance does not match, or the current sandbox cannot reach host IPC. ES does not distinguish these cases for the wrapper.

## Examples

```powershell
python "<skill-root>\scripts\es_wrapper.py" --format json -- "resume.pdf"
python "<skill-root>\scripts\es_wrapper.py" --format json -- -regex "^test.*\.js$"
python "<skill-root>\scripts\es_wrapper.py" --format json -- -sort size -sort-descending "*.iso"
python "<skill-root>\scripts\es_wrapper.py" --format json -- /ad "project"
python "<skill-root>\scripts\es_wrapper.py" --format text --output-limit -1 -- -export-efu "C:\Exports\music.efu" "*.mp3"
```
