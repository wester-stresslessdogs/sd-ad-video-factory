#!/usr/bin/env bash
# Serve the workflow flow map on localhost with live-reload.
# The page polls flow.json every 1.5s, so edits to flow.json show up live.
cd "$(dirname "$0")"
PORT="${1:-8777}"
echo "Workflow flow map → http://localhost:${PORT}/"
echo "Edit flow.json and the page updates itself. Ctrl-C to stop."
python3 -m http.server "$PORT"
