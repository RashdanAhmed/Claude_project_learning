# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

GRC Task Desk: a day-to-day task list for governance, risk and compliance work (tasks, projects, per-project routine libraries, pictures, a 30-day recycle bin). One page runs on three hosts, each keeping its own data:

| Host | Entry point | Storage |
| --- | --- | --- |
| Local app (primary) | `app/server.py` serving `app/static/index.html` | SQLite + picture files in `app/data/` |
| claude.ai artifact | `grc-task-desk.html`, published to https://claude.ai/artifact/He8zB2nNySD9ZLbnuKL2Xo | the artifact's `db` and `assets` capabilities |
| Single file | `grc-task-desk-standalone.html` opened from disk | `localStorage` (records) + IndexedDB (pictures) |

## Commands

There is no package manager, test suite or linter. Python 3.8+ standard library and plain browser JS only.

```sh
python3 build.py                                   # regenerate both built copies after editing grc-task-desk.html
python3 app/server.py --open                       # run the app at http://localhost:8765/
python3 app/server.py --port 8799 --data /some/tmp/dir   # run against throwaway data
python3 -m py_compile app/server.py build.py       # syntax-check the Python
# syntax-check the page script:
python3 -c "import re;open('/tmp/page.js','w').write(re.search(r'<script>(.*)</script>',open('grc-task-desk.html').read(),re.S).group(1))" && node --check /tmp/page.js
```

## Single source, generated copies

`grc-task-desk.html` is the only page source. It deliberately has no `<!doctype>`, `<html>`, `<head>` or `<body>`: claude.ai adds that skeleton when it publishes. `build.py` adds it for the other two hosts by splitting the file at its first `</style>` (everything before goes in `<head>`), and it injects `<meta name="grc-task-desk-api" content="/api">` into the app's copy only.

- Never edit `grc-task-desk-standalone.html` or `app/static/index.html` by hand; edit the source and run `python3 build.py`. The built copies are committed.
- Keep exactly one `<style>` block ahead of the markup, or the head/body split breaks.
- After changing the source, republish it to the claude.ai artifact (same file path, same URL). Its declared capabilities are `db`, `user` and `assets`; omit `capabilities` on a republish to keep them.

## Page architecture (`grc-task-desk.html`)

Everything is one IIFE of vanilla JS with no framework or build step.

- **Host detection**: `env` is `"server"` when the API meta tag is present, `"claude"` when `window.claude.use` exists, otherwise `"browser"`. `mode` tracks connection state (`connecting`, `server`, `offline`, `synced`, `browser`, `local`, `error`). Use `dataLoaded()` before acting on "missing" data, so a failed load can't reset preferences or purge anything.
- **Data model**: three collections, `COLLS = ["tasks", "projects", "routines"]`, held in `Map`s (`MAPS`). Every record passes through its normalizer (`normTask`, `normProject`, `normRoutine`) on load and write, so stored documents can be partial or old. Adding a field means adding it to the normalizer. Adding a collection means updating `COLLS`/`MAPS`/`NORM` here and `COLLECTIONS` in `app/server.py`.
- **Writes**: all writes go through `putMany`/`dropMany` (`put`/`drop` wrap them). They update the map, call `render()` once, then send the writes through one serial promise chain (`track`) to whichever backend `env` selects: `api()` for the server, `db.collection().doc().set()` on claude.ai, `persistLocal()` for the single file. Batch related changes into one `putMany` call rather than looping `put`.
- **Rendering**: `render()` rebuilds every region from state with `innerHTML` and template strings. Escape all user text with `esc()`. Lists keep keyboard focus across rebuilds by element `id` (`renderList(now, focusTo)`, `ui.libFocus`), so interactive elements inside rebuilt regions need stable ids. Per-viewer conveniences (view, project filter, library) live in `ui` and are saved with `prefs`, which wraps `localStorage`.
- **Recycle bin**: deleting a task sets `deletedAt` (`moveToBin`) and nothing is removed. Views and counts use `liveTasks()`, the Bin view uses `binTasks()`. `purgeExpired()` permanently deletes tasks binned more than `BIN_DAYS` (30) ago, with their pictures. It runs once data has loaded and when the date rolls over.
- **Routines**: a task added from a routine stores the routine's id in `task.routine`, which drives "On your desk"; older tasks fall back to matching project and title (`routineKey`). Routines whose project no longer exists count as General. Removing a project rewrites its routines to `project: ""`.
- **Pictures**: tasks store picture ids only. `pics` uploads and deletes through the server API, claude.ai `assets`, or IndexedDB depending on `env`. The task editor deletes pictures added and then cancelled (`ed.added`); the server also sweeps unreferenced pictures older than a day when it starts.
- **Dialogs**: use `openDialog`/`closeDialog`/`closeOnBackdrop`. `toast()` moves itself into the topmost open `<dialog>` so it isn't hidden behind the modal.

## App server (`app/server.py`)

- One table per collection, each `(id, body JSON, updated_at)`. Tables are created on startup, so a running server must be restarted to pick up a new collection; until then, writes to it 404.
- API: `GET /api/state` (everything plus `revision`), `GET /api/revision` (pages poll it every 10 s to pick up other tabs' changes), `PUT`/`DELETE /api/<collection>/<id>`, `POST /api/pictures` (raw image body; the type is judged from its bytes, PNG/JPEG/GIF/WebP only), `GET`/`DELETE /api/pictures/<id>`, `GET /api/backup` (zip laid out like the data folder).
- Security model: binds to 127.0.0.1 by default; rejects unknown `Host` headers (DNS rebinding) unless started with a non-loopback `--host`; refuses cross-origin writes by `Origin`; requires JSON or image content types (which forces a CORS preflight that it never answers); caps request bodies; sends a CSP. There is no authentication, by design, so keep these checks when changing routes.
- `start.bat` (CRLF, enforced by `.gitattributes`) and `start.command` (must stay executable) are the double-click launchers.

## Verifying changes

Chromium and Playwright are preinstalled (`require('playwright')`). Test the app against a throwaway `--data` directory, and test the single file via a `file://` URL.

- Ticking a task's checkbox can move it out of the current view (recurring tasks roll to their next due date), so use a single `click()` rather than Playwright's `check()`, which keeps retrying on the next row.
- When stopping a background server, match the process anchored to its start (`pkill -f '^python3 server.py --port 8799'`). An unanchored pattern also matches the shell running the command and kills it.
