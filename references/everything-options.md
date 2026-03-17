# Everything.exe options reference

## Purpose

Use `Everything.exe` options to control the Everything app itself: startup behavior, window state, search state, EFU lists, services, installation, and database operations.

Syntax:

```powershell
Everything.exe [filename] [options]
```

## Search-related

- `-search <text>` / `-s <text>`
- `-regex`, `-noregex`
- `-case`, `-nocase`
- `-wholeword`, `-nowholeword`
- `-matchpath`, `-nomatchpath`
- `-path <path>` / `-p <path>`
- `-parent <path>`
- `-parentpath <path>`
- `-filename <filename>`
- `-name-part <filename>`
- `-filter <name>`
- `-bookmark <name>`
- `-home`
- `-url <es:search>`
- `-search-file-list <filename>`

## Results/view

- `-sort <name>`
- `-sort-ascending`
- `-sort-descending`
- `-details`
- `-thumbnails`
- `-thumbnail-size <size>`
- `-focus-top-result`
- `-focus-bottom-result`
- `-focus-last-run-result`
- `-focus-most-run-result`
- `-focus-results`
- `-select <filename>`

## Window/app behavior

- `-startup` — run in background
- `-newwindow`, `-nonewwindow`
- `-toggle-window`
- `-close`
- `-fullscreen`, `-nofullscreen`
- `-maximized`, `-nomaximized`
- `-minimized`, `-nominimized`
- `-ontop`, `-noontop`
- `-first-instance`
- `-no-first-instance`
- `-exit` / `-quit`
- `-instance <name>`

## Database

- `-db <filename>`
- `-read-only`
- `-reindex`
- `-update`
- `-nodb`
- `-load-delay <ms>`

## EFU / file lists

- `[filename]` — open a file list
- `-f <filename>` / `-filelist <filename>`
- `-edit <filename>` — open file list editor
- `-create-file-list <filename> <path>`
- `-create-file-list-exclude-files <filters>`
- `-create-file-list-exclude-folders <filters>`
- `-create-file-list-include-only-files <filters>`

Example:

```powershell
Everything.exe -create-file-list "music.efu" "D:\Music" -create-file-list-include-only "*.mp3;*.flac"
```

## Services / instances / connection

- `-connect <[username[:password]@]host[:port]>`
- `-admin-server-share-links`, `-server-share-links`, `-ftp-links`, `-drive-links`
- `-start-service`, `-stop-service`
- `-start-client-service`, `-stop-client-service`
- `-service-port <port>`
- `-service-pipe-name <name>`
- `-svc`, `-svc-port <port>`, `-svc-pipe-name <name>`, `-svc-security-descriptor <sd>`
- `-client-svc`

## Install/uninstall and setup

Treat these as sensitive.

- `-install <location>`
- `-install-options <command line options>`
- `-uninstall [path]`
- `-uninstall-user`
- `-install-service`, `-uninstall-service`
- `-install-client-service`, `-uninstall-client-service`
- `-install-desktop-shortcut`, `-uninstall-desktop-shortcut`
- `-install-start-menu-shortcuts`, `-uninstall-start-menu-shortcuts`
- `-install-quick-launch-shortcut`, `-uninstall-quick-launch-shortcut`
- `-install-run-on-system-startup`, `-uninstall-run-on-system-startup`
- `-install-folder-context-menu`, `-uninstall-folder-context-menu`
- `-install-efu-association`, `-uninstall-efu-association`
- `-install-url-protocol`, `-uninstall-url-protocol`
- `-install-config <filename>`
- `-language <langID>`
- `-choose-language`
- `-choose-volumes`
- `-enable-run-as-admin`, `-disable-run-as-admin`
- `-enable-update-notification`, `-disable-update-notification`
- `-app-data`, `-noapp-data`

## USN journal

Also sensitive/admin-level:

- `-create-usn-journal <volume> <max-size-bytes> <allocation-delta-bytes>`
- `-delete-usn-journal <volume>`

## Multi-file rename UI

These show Everything's multi-file rename dialog without opening normal search use:

- `-copyto [files...]`
- `-moveto [files...]`
- `-rename [files...]`

## Notes

- Many dashed names can omit the extra dash, e.g. `-nonewwindow`.
- Quote paths with spaces.
- Some admin-required options will relaunch Everything elevated.
- Prefer `es.exe` instead when the task is purely CLI search/export against an already running instance.
