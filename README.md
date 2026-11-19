# x402 AVM Examples

[![CI](https://github.com/x402-avm/examples/actions/workflows/ci.yml/badge.svg)](https://github.com/x402-avm/examples/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node 20+](https://img.shields.io/badge/node-20+-green.svg)](https://nodejs.org/)

Runnable code examples demonstrating the `x402` payment protocol on Algorand across LocalNet, TestNet, and MainNet in Python and TypeScript / JavaScript.

The repository covers end-to-end payment flows: FastMCP tool monetization, FastAPI and Flask middleware paywalls, dynamic pricing, vendor-scoped passes, cryptographic wallet identity proofs, settle-on-success guarantees, and public network read-only simulations.

Documentation: https://x402-avm.github.io

## Examples Directory

| Example | Description | Network | Language | Command | Expected Output |
|---|---|---|---|---|---|
| [manual_flow.py](localnet/manual_flow.py) | Low-level Exact AVM scheme verification and settlement (`PayerAvmSigner` + `ServerAvmSigner`) | LocalNet | Python | `python localnet/manual_flow.py` | Verified payment, confirmed round |
| [identity.py](localnet/identity.py) | Off-chain wallet identity proof (`X-Identity-Txn`) | LocalNet | Python | `python localnet/identity.py` | Verified address matches: True |
| [identity.mjs](localnet/identity.mjs) | Wallet identity proof generation and verification | LocalNet | JavaScript | `node localnet/identity.mjs` | Identity proof verified successfully |
| [pricing.py](localnet/pricing.py) | Fixed, dynamic arguments, and bulk discount pricing | LocalNet | Python | `python localnet/pricing.py` | Three calls with verified charges |
| [passes.py](localnet/passes.py) | Vendor-scoped passes via receipt transaction notes | LocalNet | Python | `python localnet/passes.py` | Call 1: 5000 microALGO, Call 2: 0 |
| [failed_call_not_charged.py](localnet/failed_call_not_charged.py) | Settle-on-success guarantee on tool exception | LocalNet | Python | `python localnet/failed_call_not_charged.py` | Tool error returned, balance drop: 0 |
| [networks.py](localnet/networks.py) | Network CAIP-2 ID, genesis hash, and endpoint inspector | Multi | Python | `python localnet/networks.py` | Formatted table of network settings |
| [quickstart_server.py](localnet/quickstart_server.py) | FastMCP paid tool server over Streamable HTTP (port 9201, `/mcp`) | LocalNet | Python | `python localnet/quickstart_server.py` | Server listening on port 9201 |
| [quickstart_client.py](localnet/quickstart_client.py) | `paid_mcp_session` client (Streamable HTTP) with `AIEconomyError` handling | LocalNet | Python | `python localnet/quickstart_client.py` | Result: echo, balance drop: 5000 |
| [fastapi_paywall.py](localnet/fastapi_paywall.py) | FastAPI paywall with the shipped `ServerAvmSigner` (about 35 lines) | LocalNet | Python | `python localnet/fastapi_paywall.py` | Server listening on port 9211 |
| [flask_paywall.py](localnet/flask_paywall.py) | Flask paywall with the shipped `ServerAvmSigner` | LocalNet | Python | `python localnet/flask_paywall.py` | Server listening on port 9212 |
| [httpx_client.py](localnet/httpx_client.py) | Automated payment HTTPX client (`PayerAvmSigner`) | LocalNet | Python | `python localnet/httpx_client.py` | HTTP 200, balance drop: 10000 |
| [server_for_js.py](localnet/server_for_js.py) | FastAPI paywall server for JavaScript client tests | LocalNet | Python | `python localnet/server_for_js.py` | Server listening on port 9221 |
| [js_pay.mjs](localnet/js_pay.mjs) | JavaScript x402 client with explicit spend controls and typed errors | LocalNet | JavaScript | `node localnet/js_pay.mjs` | HTTP 200, balance drop: 5000 |
| [browser_wallet.ts](localnet/browser_wallet.ts) | React browser wallet integration wrapper | LocalNet / Web | TypeScript | `npm run typecheck` | Type check passes |
| [paid_mcp_tool](localnet/paid_mcp_tool/) | Paid summarize tool with dynamic length pricing | LocalNet | Python | `python localnet/paid_mcp_tool/server.py` | Summarize tool on port 9231 (`/mcp`) |
| [browser_paywall](localnet/browser_paywall/) | Complete browser paywall with frontend bundle | LocalNet | Python / JS | `python localnet/browser_paywall/server.py` | Web paywall on port 9232 |
| [testnet/simulate.py](testnet/simulate.py) | Read-only simulation for ALGO and USDC on TestNet | TestNet | Python | `python testnet/simulate.py` | All 4 TestNet simulations: ok |
| [testnet/simulate.mjs](testnet/simulate.mjs) | Read-only simulation for ALGO and USDC on TestNet | TestNet | JavaScript | `node testnet/simulate.mjs` | All 4 TestNet simulations: ok |
| [testnet/live_payment.py](testnet/live_payment.py) | Real TestNet payment (requires env vars; else exits 0) | TestNet | Python | `python testnet/live_payment.py` | Settled transaction ID (or skipped) |
| [mainnet/simulate.py](mainnet/simulate.py) | Read-only simulation for ALGO and USDC on MainNet | MainNet | Python | `python mainnet/simulate.py` | All 4 MainNet simulations: ok |
| [mainnet/simulate.mjs](mainnet/simulate.mjs) | Read-only simulation for ALGO and USDC on MainNet | MainNet | JavaScript | `node mainnet/simulate.mjs` | All 4 MainNet simulations: ok |
| [shared/config.py](shared/config.py) | Multi-network config manager and dry run inspector | Multi | Python | `python shared/config.py --dry-run` | Configuration matrix (0 txns sent) |

## Prerequisites

1. **Python**: Python 3.10+ (tested on Python 3.10 through 3.14).
2. **Node.js**: Node 20, 22, or 24.
3. **AlgoKit LocalNet**: Needed for running the LocalNet examples:
   ```bash
   pipx install algokit
   algokit localnet start
   ```

## Installation

### Python
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### JavaScript
```bash
npm install
```

## Running the Examples

### Run All LocalNet Examples
To run every LocalNet example sequentially with automatic server lifecycle management and port verification:
```bash
bash scripts/run_all_localnet.sh
```

### Run Public Network Simulations (Read-Only)
The simulation examples evaluate valid transaction groups on live TestNet and MainNet nodes using Algod's simulate endpoint with zero spend:
```bash
# TestNet
python testnet/simulate.py
node testnet/simulate.mjs

# MainNet
python mainnet/simulate.py
node mainnet/simulate.mjs
```

### Optional Live TestNet Payment
To execute a real payment transaction on TestNet, set funded 25-word account mnemonics:
```bash
export TESTNET_BUYER_MNEMONIC="word1 word2 ... word25"
export TESTNET_SERVER_MNEMONIC="word1 word2 ... word25"
python testnet/live_payment.py
```
*(Free TestNet ALGO can be dispensed from https://lora.algokit.io/testnet/fund. If the environment variables are unset, the script exits cleanly with status 0).*

## Port Allocations

LocalNet examples run on dedicated non-conflicting loopback ports:
- `9201`: Quickstart Server
- `9202`: Pricing Server
- `9203`: Passes Server
- `9204`: Failed Call Server
- `9211`: FastAPI Paywall Server
- `9212`: Flask Paywall Server
- `9221`: JavaScript Paywall Server
- `9231`: Paid MCP Tool Server
- `9232`: Browser Paywall Server

## Related Repositories

- [ai-economy-sdk](https://github.com/x402-avm/ai-economy-sdk): MCP payment gating, dynamic pricing, passes, and identity verification.
- [x402-algorand](https://github.com/x402-avm/x402-algorand): Algorand exact payment scheme plugin for the official `x402` Python SDK.
- [x402-avm-js](https://github.com/x402-avm/x402-avm-js): Browser and Node.js client library for x402 payments on Algorand.

## License

MIT License. See [LICENSE](LICENSE) for details.
