# es.exe reference

## Purpose

Use `es.exe` for command-line searching against a running Everything instance.

Syntax:

```powershell
es.exe [options] [search text]
```

## Common flags

### Matching

- `-regex` — regex search
- `-case` — case-sensitive match
- `-whole-word` / `-ww` — whole-word match
- `-match-path` / `-p` — match full path and file name
- `-diacritics` — diacritic-sensitive match

### Scope and paging

- `-offset <n>` — zero-based result offset
- `-max-results <n>` / `-n <n>` — limit result count
- `-path <path>` — search within a path tree
- `-parent-path <path>` — search a parent path
- `-parent <path>` — search only direct children
- `/ad` — folders only
- `/a-d` — files only
- `/a[attributes]` — filter by attributes

### Sort and columns

- `-sort <field>` — sort by a field
- `-sort-ascending` / `-sort-descending`
- `-name`, `-path-column`, `-full-path-and-name`, `-extension`, `-size`, `-date-modified`, `-dm`, `-date-created`, `-dc`, `-date-accessed`, `-da`, `-attributes`, `-run-count`, `-date-run`, `-date-recently-changed`, `-rc`

Common sort fields:

- `name`
- `path`
- `size`
- `extension`
- `date-created`
- `date-modified` / `dm`
- `date-accessed`
- `attributes`
- `run-count`
- `date-run`
- `date-recently-changed`

DIR-style sort aliases also exist, such as `/oN`, `/o-N`, `/oS`, `/o-S`, `/oE`, `/oD`.

### Output/export

- `-csv`, `-efu`, `-txt`, `-m3u`, `-m3u8` — change output format
- `-export-csv <file>`
- `-export-efu <file>`
- `-export-txt <file>`
- `-export-m3u <file>`
- `-export-m3u8 <file>`
- `-highlight`, `-highlight-color <color>`
- `-pause` / `-more`

### Misc

- `-instance <name>` — connect to a named Everything instance
- `-timeout <ms>` — wait for DB load
- `-help`
- `-save-settings`, `-clear-settings`
- `-set-run-count <filename> <count>`
- `-inc-run-count <filename>`
- `-get-run-count <filename>`

## Examples

```powershell
es.exe foo
es.exe -regex "^test.*\.js$"
es.exe -sort size -n 10
es.exe -sort dm -n 10
es.exe foo bar -highlight
es.exe *.mp3 -export-efu mp3.efu
es.exe -path "D:\Projects" /a-d -sort date-modified -sort-descending -n 20
```

## Notes

- Short dashes can often be simplified, e.g. `-nodigitgrouping` instead of `-no-digit-grouping`.
- Use quotes around paths or searches with spaces.
- `es.exe` requires Everything to be installed and running.
- Return code `8` commonly means the Everything IPC window was not found, usually because Everything is not running.
