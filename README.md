# x402-avm examples

[![CI](https://github.com/x402-avm/examples/actions/workflows/ci.yml/badge.svg)](https://github.com/x402-avm/examples/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Working code for every way to use [x402-avm](https://github.com/x402-avm/x402-avm): selling MCP tools, paywalling HTTP APIs, and paying from Python, agents, browsers and Node.js, on Algorand. Every example uses the published packages, and CI runs them on LocalNet.

The [documentation](https://x402-avm.github.io) explains each one. Start with the [Quickstart](https://x402-avm.github.io/quickstart).

## Set up once

You need Python 3.10+, Node.js 20+, Docker and [AlgoKit](https://github.com/algorandfoundation/algokit-cli). LocalNet is a private Algorand network on your machine with free test money, and the examples fund their own accounts from it.

```bash
algokit localnet start
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
npm install
```

Run servers in one terminal and clients in another. `bash scripts/run_all_localnet.sh` runs everything in order, starting and stopping the servers for you.

## Start here

| Example | What you'll see |
|---|---|
| [`quickstart_server.py`](localnet/quickstart_server.py) + [`quickstart_client.py`](localnet/quickstart_client.py) | A tool that costs 0.005 ALGO per call, and a client paying for it. Prints `Balance drop: 5000 microALGO` |
| [`failed_call_not_charged.py`](localnet/failed_call_not_charged.py) | A tool that fails costs the buyer nothing. Prints a balance drop of 0 |

## Sell MCP tools

| Example | What you'll see |
|---|---|
| [`paid_mcp_tool/`](localnet/paid_mcp_tool/) | A summarize tool whose price depends on the length asked for |
| [`pricing.py`](localnet/pricing.py) | Fixed prices, prices computed from the arguments, and bulk discounts |
| [`passes.py`](localnet/passes.py) | Pay once for a pass, then call for free: the first call costs 5000 microALGO, the second 0 |
| [`identity.py`](localnet/identity.py) | A caller proving it owns an address, without a transaction |

## Paywall an HTTP API

| Example | What you'll see |
|---|---|
| [`fastapi_paywall.py`](localnet/fastapi_paywall.py) | A FastAPI route that costs 0.01 ALGO, in about 35 lines |
| [`flask_paywall.py`](localnet/flask_paywall.py) | The same with Flask |
| [`httpx_client.py`](localnet/httpx_client.py) | A Python client paying for it automatically |
| [`manual_flow.py`](localnet/manual_flow.py) | Each step of verifying and settling a payment, done by hand |

## Pay from JavaScript

| Example | What you'll see |
|---|---|
| [`js_pay.mjs`](localnet/js_pay.mjs) (server: [`server_for_js.py`](localnet/server_for_js.py)) | Node.js paying a 402, with spend limits and typed errors |
| [`browser_paywall/`](localnet/browser_paywall/) | A complete web page that pays from a wallet |
| [`browser_wallet.ts`](localnet/browser_wallet.ts) | React integration with `use-wallet-react`, for Pera, Defly and other wallets |
| [`identity.mjs`](localnet/identity.mjs) | An identity proof from JavaScript |

## Go to TestNet and MainNet

The simulation examples check payments against the public networks without spending anything, using the node's `simulate` endpoint.

| Example | What you'll see |
|---|---|
| [`testnet/simulate.py`](testnet/simulate.py), [`simulate.mjs`](testnet/simulate.mjs) | ALGO and USDC payments that would succeed on TestNet |
| [`mainnet/simulate.py`](mainnet/simulate.py), [`simulate.mjs`](mainnet/simulate.mjs) | The same on MainNet. Nothing is sent |
| [`testnet/live_payment.py`](testnet/live_payment.py) | A real TestNet payment. Set `TESTNET_BUYER_MNEMONIC` and `TESTNET_SERVER_MNEMONIC` first (free TestNet ALGO from the [dispenser](https://lora.algokit.io/testnet/fund)); without them it skips |
| [`localnet/networks.py`](localnet/networks.py), [`shared/config.py`](shared/config.py) | Network ids, endpoints and USDC asset ids for each network |

## Ports

Each LocalNet server has its own port, so several can run at once: quickstart 9201, pricing 9202, passes 9203, failed call 9204, FastAPI 9211, Flask 9212, JavaScript 9221, paid MCP tool 9231, browser paywall 9232.

## Licence

MIT. See [LICENSE](LICENSE).
