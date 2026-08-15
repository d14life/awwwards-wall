#!/bin/sh
# Wait for any running download, then fill gaps, transcode, rebuild manifest.
set -e
cd "$(dirname "$0")"

while pgrep -f "python3 download.py" > /dev/null 2>&1; do sleep 10; done

python3 download.py
python3 transcode.py
python3 make_manifest.py
echo "BUILD DONE: $(find web -name '*.mp4' | wc -l) proxies, $(du -sh web | cut -f1)"
