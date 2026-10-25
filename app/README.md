# GRC Task Desk app

Runs GRC Task Desk on your own computer as a small web app. Your tasks, projects and pictures are kept in the `data` folder next to the app and never leave your computer. The only thing the page loads from the internet is its fonts. Offline, it uses your system fonts.

## What you need

Python 3.8 or later. There is nothing else to install.

- **Windows**: install Python from https://www.python.org/downloads/
- **macOS**: run `python3 --version` in Terminal. If Python is missing, macOS offers to install it, or use python.org.
- **Linux**: Python 3 is usually already installed.

## Start it

- **Windows**: double-click `start.bat`.
- **macOS**: double-click `start.command`. The first time, macOS may block it because it was downloaded. Right-click it, choose **Open**, then **Open** again.
- **Any system, from a terminal**: `python3 server.py --open` (on Windows, `py server.py --open`).

Your browser opens http://localhost:8765/. Bookmark it. The window that opened with the app is the app: keep it open while you work, and close it (or press Ctrl+C) to stop the app.

## Options

```sh
python3 server.py --port 9000            # use another port if 8765 is taken
python3 server.py --data "D:\GRC data"   # keep your data somewhere else, such as a backed-up drive
python3 server.py --host 0.0.0.0         # let other computers on your network open it
python3 server.py --help                 # list every option
```

With `--host 0.0.0.0`, colleagues can open the address the app prints, such as `http://192.168.1.20:8765/`. The app has no sign-in, so anyone who can reach your computer on that port can read and change your tasks. Only do this on a network you trust. Your firewall may ask you to allow it.

## Your data

| What | Where |
| --- | --- |
| Tasks and projects | `data/grc-task-desk.db` (a SQLite database) |
| Pictures | `data/pictures/` |

- **Back up**: in the app, open **Configuration → Download backup**. Or stop the app and copy the `data` folder.
- **Restore**: stop the app, unzip the backup into the `data` folder (replacing what's there), then start the app.
- **Update the app**: replace `server.py`, `static/` and the start files with the new versions. Keep your `data` folder.

Pictures you add to a task but never save are cleaned up automatically the next time the app starts, once they're a day old.

## Start it automatically (optional)

- **Windows**: press Win+R, type `shell:startup`, and put a shortcut to `start.bat` in the folder that opens.
- **macOS**: open **System Settings → General → Login Items** and add `start.command`.
