#!/usr/bin/env bash
set -euo pipefail

HOST="127.0.0.1"
PORT="${PORT:-18080}"
TMP_DIR="$(mktemp -d)"
EVENTS="$TMP_DIR/events.jsonl"
PAGE="$TMP_DIR/page.html"
SERVER_PID=""

cleanup() {
    if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi
    rm -rf "$TMP_DIR"
}
trap cleanup EXIT

python3 honeypot.py --host "$HOST" --port "$PORT" >"$EVENTS" 2>&1 &
SERVER_PID=$!

ready=0
for _ in {1..40}; do
    if ! kill -0 "$SERVER_PID" 2>/dev/null; then
        cat "$EVENTS" >&2
        echo "The honeypot stopped before it was ready. Check whether port $PORT is already in use." >&2
        exit 1
    fi
    if curl --noproxy '*' --connect-timeout 1 --silent --output /dev/null "http://$HOST:$PORT/"; then
        ready=1
        break
    fi
    sleep 0.1
done

if [[ "$ready" -ne 1 ]]; then
    echo "The honeypot did not become ready at http://$HOST:$PORT/." >&2
    exit 1
fi

get_status="$(curl --noproxy '*' --silent --show-error --output "$PAGE" --write-out '%{http_code}' "http://$HOST:$PORT/")"
post_status="$(curl --noproxy '*' --silent --show-error --output /dev/null --write-out '%{http_code}' \
    --request POST --data 'username=demo-user&password=fake-test-only' "http://$HOST:$PORT/session")"

if [[ "$get_status" != "200" ]]; then
    echo "Expected GET / to return 200; received $get_status." >&2
    exit 1
fi
if [[ "$post_status" != "401" ]]; then
    echo "Expected POST /session to return 401; received $post_status." >&2
    exit 1
fi
if ! grep -q 'Northstar Operations Portal' "$PAGE"; then
    echo "The response did not contain the fictional demo portal." >&2
    exit 1
fi
if grep -Eq 'demo-user|fake-test-only' "$EVENTS"; then
    echo "A sample form value appeared in the event log." >&2
    exit 1
fi
if ! grep -q '"body_bytes":' "$EVENTS"; then
    echo "The event log did not include the request body size." >&2
    exit 1
fi

printf 'GET / -> HTTP %s\n' "$get_status"
printf 'POST /session with synthetic values -> HTTP %s\n' "$post_status"
echo "PASS: request metadata was recorded; sample form values were not logged."
