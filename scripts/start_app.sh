#!/usr/bin/env bash
# Start the Content Portal in the background and wait until /api/health answers.
# Usage: bash scripts/start_app.sh (Flask dev server)
# bash scripts/start_app.sh waitress (multi-threaded server for load tests)
set -euo pipefail
SERVER="${1:-flask}"
mkdir -p reports
if [ "$SERVER" = "waitress" ]; then
    nohup waitress-serve --host=127.0.0.1 --port=5000 --threads=8 --ident=content-portal \
        app.portal:app > reports/app.log 2>&1 &
else
    nohup python app/portal.py > reports/app.log 2>&1 &
fi
for _ in $(seq 1 30); do
    if curl -fsS http://127.0.0.1:5000/api/health > /dev/null 2>&1; then
        echo "Content Portal is up ($SERVER)"
        exit 0
    fi
    sleep 1
done
echo "Content Portal did not start. Log:"
cat reports/app.log
exit 1
