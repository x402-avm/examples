#!/usr/bin/env bash
set -eo pipefail

echo "======================================================================"
echo " Running All LocalNet Examples (x402-avm/examples)"
echo "======================================================================"

PYTHON="${PYTHON:-python3}"
NODE="${NODE:-node}"

# Check Algod health
echo "Checking LocalNet Algod on http://localhost:4001/health..."
if ! curl -sf http://localhost:4001/health > /dev/null; then
    echo "ERROR: LocalNet Algod is not responding at http://localhost:4001. Start LocalNet before running this script." >&2
    exit 1
fi
echo "LocalNet is UP."

STARTED_PIDS=()

cleanup() {
    echo "--- Cleaning up background processes ---"
    for pid in "${STARTED_PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping server process $pid..."
            kill -TERM "$pid" 2>/dev/null || true
            wait "$pid" 2>/dev/null || true
        fi
    done
    STARTED_PIDS=()
}

trap cleanup EXIT INT TERM

wait_for_port() {
    local port="$1"
    local max_wait=30
    local count=0
    while ! nc -z 127.0.0.1 "$port" 2>/dev/null; do
        sleep 0.2
        count=$((count + 1))
        if [ "$count" -ge $((max_wait * 5)) ]; then
            echo "ERROR: Port $port did not open within $max_wait seconds." >&2
            return 1
        fi
    done
}

stop_pid() {
    local pid="$1"
    if kill -0 "$pid" 2>/dev/null; then
        kill -TERM "$pid" 2>/dev/null || true
        wait "$pid" 2>/dev/null || true
    fi
}

echo ""
echo "[1/13] Running manual_flow.py (Exact AVM scheme flow)..."
"$PYTHON" localnet/manual_flow.py

echo ""
echo "[2/13] Running identity.py (Python X-Identity-Txn verification)..."
"$PYTHON" localnet/identity.py

echo ""
echo "[3/13] Running identity.mjs (JavaScript X-Identity-Txn verification)..."
"$NODE" localnet/identity.mjs

echo ""
echo "[4/13] Running pricing.py (Fixed, dynamic, and bulk pricing on port 9202)..."
"$PYTHON" localnet/pricing.py

echo ""
echo "[5/13] Running passes.py (Vendor-scoped passes on port 9203)..."
"$PYTHON" localnet/passes.py

echo ""
echo "[6/13] Running failed_call_not_charged.py (Settle-on-success on port 9204)..."
"$PYTHON" localnet/failed_call_not_charged.py

echo ""
echo "[7/13] Running networks.py (Network parameter inspector)..."
"$PYTHON" localnet/networks.py

echo ""
echo "[8/13] Running Quickstart Server & Client (port 9201)..."
"$PYTHON" localnet/quickstart_server.py &
SERVER_PID=$!
STARTED_PIDS+=("$SERVER_PID")
wait_for_port 9201
"$PYTHON" localnet/quickstart_client.py
stop_pid "$SERVER_PID"

echo ""
echo "[9/13] Running FastAPI Paywall & HTTPX Client (port 9211)..."
"$PYTHON" localnet/fastapi_paywall.py &
SERVER_PID=$!
STARTED_PIDS+=("$SERVER_PID")
wait_for_port 9211
"$PYTHON" localnet/httpx_client.py --url http://127.0.0.1:9211/weather
stop_pid "$SERVER_PID"

echo ""
echo "[10/13] Running Flask Paywall & HTTPX Client (port 9212)..."
"$PYTHON" localnet/flask_paywall.py &
SERVER_PID=$!
STARTED_PIDS+=("$SERVER_PID")
wait_for_port 9212
"$PYTHON" localnet/httpx_client.py --url http://127.0.0.1:9212/weather
stop_pid "$SERVER_PID"

echo ""
echo "[11/13] Running Server for JS & JS Pay Client (port 9221)..."
"$PYTHON" localnet/server_for_js.py &
SERVER_PID=$!
STARTED_PIDS+=("$SERVER_PID")
wait_for_port 9221
"$NODE" localnet/js_pay.mjs
stop_pid "$SERVER_PID"

echo ""
echo "[12/13] Running Paid MCP Tool Server & Client (port 9231)..."
"$PYTHON" localnet/paid_mcp_tool/server.py &
SERVER_PID=$!
STARTED_PIDS+=("$SERVER_PID")
wait_for_port 9231
"$PYTHON" localnet/paid_mcp_tool/client.py
stop_pid "$SERVER_PID"

echo ""
echo "[13/13] Running Browser Paywall Server & Verify Client (port 9232)..."
echo "Building browser paywall frontend bundle (bundle.js) with esbuild..."
if [ -x "./node_modules/.bin/esbuild" ]; then
    ./node_modules/.bin/esbuild localnet/browser_paywall/app.js --bundle --outfile=localnet/browser_paywall/bundle.js --format=esm
elif command -v npx >/dev/null 2>&1; then
    npx esbuild localnet/browser_paywall/app.js --bundle --outfile=localnet/browser_paywall/bundle.js --format=esm
elif command -v esbuild >/dev/null 2>&1; then
    esbuild localnet/browser_paywall/app.js --bundle --outfile=localnet/browser_paywall/bundle.js --format=esm
else
    echo "ERROR: esbuild not found in ./node_modules/.bin or PATH" >&2
    exit 1
fi
"$PYTHON" localnet/browser_paywall/server.py &
SERVER_PID=$!
STARTED_PIDS+=("$SERVER_PID")
wait_for_port 9232
"$NODE" localnet/browser_paywall/verify.mjs
stop_pid "$SERVER_PID"

# Explicit cleanup of any remaining background processes
cleanup

echo ""
echo "--- Verifying ports 9200-9239 are completely free ---"
sleep 1
BUSY_PORTS=$(ss -tulpn 2>/dev/null | grep -E ":(92[0-3][0-9])" || true)
if [ -n "$BUSY_PORTS" ]; then
    echo "ERROR: Ports still in use:" >&2
    echo "$BUSY_PORTS" >&2
    exit 1
fi
echo "Ports 9200-9239 are completely free."

echo ""
echo "======================================================================"
echo " ALL 13 LOCALNET EXAMPLES PASSED SUCCESSFULLY!"
echo "======================================================================"
