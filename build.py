#!/usr/bin/env python3
"""Builds the copies of the page that run outside claude.ai from grc-task-desk.html.

grc-task-desk.html is the source published to claude.ai, which adds <html>, <head> and
<body> at publish time. This script does that wrapping for the other two hosts:

    grc-task-desk-standalone.html   opens straight from disk, saves to the browser
    app/static/index.html           served by app/server.py, saves to its database

Run it after editing grc-task-desk.html: python3 build.py
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESET = (
    "<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);"
    "padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}img{max-width:100%}"
    "[hidden]{display:none!important}</style>"
)
ICON = (
    "<link rel=\"icon\" href=\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
    "%3Crect width='32' height='32' rx='7' fill='%230D5B6C'/%3E%3Cpath d='M9 16.5l4.5 4.5L23 11' stroke='white' "
    "stroke-width='3' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E\">"
)


def page(source, extra_head):
    head, end, body = source.partition("</style>")
    if not end:
        raise SystemExit("grc-task-desk.html has no </style>; the head and body can't be told apart.")
    return "\n".join([
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
        *extra_head,
        ICON,
        RESET,
        (head + end).strip(),
        "</head>",
        "<body>",
        body.strip(),
        "</body>",
        "</html>",
        "",
    ])


def main():
    source = (ROOT / "grc-task-desk.html").read_text(encoding="utf-8")
    outputs = {
        ROOT / "grc-task-desk-standalone.html": [],
        ROOT / "app" / "static" / "index.html": ['<meta name="grc-task-desk-api" content="/api">'],
    }
    for path, extra in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(page(source, extra), encoding="utf-8", newline="\n")
        print(f"Wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
