#!/bin/sh
# Builds grc-task-desk-standalone.html, a complete HTML document that opens
# directly in a browser. grc-task-desk.html is the Artifact source, which
# claude.ai wraps in <html>/<head>/<body> at publish time; this script does
# the same wrapping for local use. Re-run it after editing grc-task-desk.html.
set -e
cd "$(dirname "$0")"
src=grc-task-desk.html
out=grc-task-desk-standalone.html
{
  printf '%s\n' '<!doctype html>' '<html lang="en">' '<head>' \
    '<meta charset="utf-8">' \
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">' \
    '<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>'
  sed -n '1,/<\/style>/p' "$src"
  printf '%s\n' '</head>' '<body>'
  sed '1,/<\/style>/d' "$src"
  printf '%s\n' '</body>' '</html>'
} > "$out"
echo "Wrote $out"
