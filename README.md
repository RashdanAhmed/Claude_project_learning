# GRC Task Desk

A day-to-day task list for governance, risk and compliance work.

## Ways to run it

| | Where your data lives | How to start |
| --- | --- | --- |
| **App on your computer** (recommended) | A database and pictures folder in `app/data` | See [`app/README.md`](app/README.md): double-click `start.bat` (Windows) or `start.command` (macOS) |
| **claude.ai page**: https://claude.ai/artifact/He8zB2nNySD9ZLbnuKL2Xo | The artifact's database on claude.ai | Open the link while signed in. It's private until you share it. |
| **Single file** [`grc-task-desk-standalone.html`](grc-task-desk-standalone.html) | Your browser's storage, on that computer only | Double-click the file |

The three don't share data: each keeps its own tasks.

## What it does

- **Triage strip**: overdue, due today, next 7 days, waiting on others, and check-ins done this week.
- **Views**: Focus (overdue, due today and in progress), Next 7 days, All open, Waiting, Recurring, Done.
- **Projects**: add, rename and remove the projects you're working on under **Configuration**, assign each task to one, and filter the desk by project. Search covers titles, notes, projects, control references and owners.
- **Due dates are set by hand**: a task can't be saved without one.
- **Notes** on every task, written when you create it and edited later.
- **Pictures**: paste a screenshot (Ctrl+V or ⌘V), drop image files, or choose them. They show as thumbnails on the task and open full size. Pasting a picture anywhere on the desk starts a new task with it.
- **Recurring tasks** (daily, weekly, monthly, quarterly, annual): ticking one logs the cycle and moves it to the next due date.
- **Routine library**: 26 standard GRC check-ins mapped to ISO/IEC 27001:2022, SOC 2, NIST CSF 2.0, PCI DSS v4.0 and GDPR references. Adding one opens the task form so you set its due date and project.
- **Task fields**: title, project, due date, notes, pictures, priority, cadence, status, area, framework, control reference, owner or stakeholder and evidence location.
- **Backup** (app only): download tasks, projects and pictures as one zip file.

## Single file notes

Tasks and projects are saved in that browser's local storage, and pictures in its IndexedDB storage. Clearing your browser's site data deletes them. If the page says **Not saved in this browser**, your browser is blocking storage for files opened from disk. Use the app instead.

## Project layout

| File | What it is |
| --- | --- |
| `grc-task-desk.html` | The page source, published to claude.ai as is |
| `build.py` | Builds the two copies below from the source |
| `grc-task-desk-standalone.html` | Built: the single-file copy |
| `app/static/index.html` | Built: the copy the app serves |
| `app/server.py` | The app's server: Python standard library only, with SQLite storage |
| `app/start.bat`, `app/start.command` | Double-click launchers for Windows and macOS |

After editing `grc-task-desk.html`, run `python3 build.py` so the single file and the app pick up the change.
