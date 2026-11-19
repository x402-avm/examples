# AGENTS.md

Guidance for AI agents working with the `x402-avm/examples` repository.

## What this repository contains

Runnable code examples demonstrating the `x402` payment protocol on Algorand across LocalNet, TestNet, and MainNet in both Python and TypeScript / JavaScript.

Documentation site: https://x402-avm.github.io

## Repository Layout

```
examples/
├── localnet/                      # Full end-to-end paid flows on Algorand LocalNet
│   ├── _localnet.py               # Shared LocalNet dispenser and account helper
│   ├── quickstart_server.py       # FastMCP paid tool server (port 9201)
│   ├── quickstart_client.py       # paid_mcp_session client
│   ├── pricing.py                 # Fixed, dynamic, and bulk pricing (port 9202)
│   ├── passes.py                  # Vendor-scoped subscription passes (port 9203)
│   ├── identity.py                # X-Identity-Txn generation and verification (Python)
│   ├── identity.mjs               # X-Identity-Txn generation and verification (Node.js)
│   ├── failed_call_not_charged.py # Settle-on-success verification (port 9204)
│   ├── fastapi_paywall.py         # x402 FastAPI payment middleware (port 9211)
│   ├── flask_paywall.py           # x402 Flask payment middleware (port 9212)
│   ├── httpx_client.py            # Client for FastAPI / Flask paywalls
│   ├── manual_flow.py             # Direct low-level ExactAvmScheme transaction flow
│   ├── server_for_js.py           # Paywall server for JavaScript client (port 9221)
│   ├── js_pay.mjs                 # JavaScript x402 client using x402-avm-js
│   ├── networks.py                # Network ID, genesis hash, and endpoint inspector
│   ├── browser_wallet.ts          # Wallet integration example (Defly, Pera, Kibisis)
│   ├── browser_paywall/           # Full web paywall tutorial (port 9232)
│   └── paid_mcp_tool/             # Paid MCP tool server and client tutorial (port 9231)
├── testnet/                       # TestNet examples (read-only simulations and safe live template)
│   ├── simulate.py                # Read-only simulate for ALGO and USDC (Python)
│   ├── simulate.mjs               # Read-only simulate for ALGO and USDC (JavaScript)
│   └── live_payment.py            # Live TestNet payment (requires env vars; otherwise exits 0)
├── mainnet/                       # MainNet examples (strictly read-only simulations)
│   ├── simulate.py                # Read-only simulate for ALGO and USDC (Python)
│   └── simulate.mjs               # Read-only simulate for ALGO and USDC (JavaScript)
├── shared/                        # Shared multi-network utilities
│   └── config.py                  # Multi-network configuration switcher
├── scripts/
│   └── run_all_localnet.sh        # Runs all LocalNet examples and verifies cleanup
├── .github/
│   ├── dependabot.yml             # Weekly dependency updates
│   └── workflows/ci.yml           # GitHub Actions workflow
├── requirements.txt               # Published Python packages
├── package.json                   # Published JavaScript packages
└── README.md                      # Overview and table of examples
```

## Setup Commands

### Python Environment
Create and activate a Python 3.12 virtual environment:
```bash
uv venv -q --python 3.12 .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### JavaScript Environment
Install Node.js dependencies:
```bash
npm install
```

## Running Examples

### 1. LocalNet Suite
Requires AlgoKit LocalNet running (`algokit localnet start`):
```bash
bash scripts/run_all_localnet.sh
```

### 2. Public Network Simulations (Read-Only)
Requires internet connection to AlgoNode public nodes:
```bash
# TestNet
python testnet/simulate.py
node testnet/simulate.mjs
python testnet/live_payment.py   # Exits 0 if credentials are not configured

# MainNet
python mainnet/simulate.py
node mainnet/simulate.mjs
python shared/config.py --dry-run
```

## Conventions

- **No Hard-Coded Paths**: Never use absolute developer paths (e.g. `/Users/...` or local usernames). Use relative paths or `Path(__file__).resolve().parent`.
- **Published Packages**: Use published package imports:
  - Python: `from ai_economy_sdk import ...`, `from x402 import ...`, `from x402_algorand import ...`
  - JavaScript: `import { ... } from 'x402-avm-js';`
- **Network Identifiers**: Use CAIP-2 standard IDs:
  - MainNet: `algorand:wGHE2Pwdvd7S12BL5FaOP20EGYesN73k`
  - TestNet: `algorand:SGO1GKSzyE7IEPItTxCByw9x8FmnrCDe`
  - LocalNet: resolved dynamically via `caip2_from_genesis_hash(sp.gh)`
- **Port Allocation**: Use designated server ports:
  - 9201: Quickstart Server
  - 9202: Pricing Server
  - 9203: Passes Server
  - 9204: Failed Call Server
  - 9211: FastAPI Paywall Server
  - 9212: Flask Paywall Server
  - 9221: JS Paywall Server
  - 9231: Paid MCP Tool Server
  - 9232: Browser Paywall Server
  - Always shut down server processes when execution completes.
- **Security**: Never commit private keys, mnemonics, or API tokens. Never submit real payments on MainNet.

## PR Checklist

- [ ] All examples run cleanly against LocalNet (`bash scripts/run_all_localnet.sh` returns 0).
- [ ] No ports in 9200-9239 are left listening after test execution.
- [ ] Public network simulate scripts execute and pass without error.
- [ ] No hard-coded user or machine paths remain in any example file.
- [ ] CI workflow YAML passes validation.
