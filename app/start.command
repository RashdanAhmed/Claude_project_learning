#!/bin/sh
# Starts GRC Task Desk and opens it in your browser (macOS and Linux).
# Keep this window open while you use the app; close it or press Ctrl+C to stop.
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then
  exec python3 server.py --open "$@"
fi
echo "Python 3 isn't installed. Download it from https://www.python.org/downloads/ and run this file again."
