"""FastMCP server payment-gated with ai-economy-sdk on Algorand LocalNet.

Runs a FastMCP server with a single paid 'echo' tool priced at 5,000 microALGO.
Funds a server account from LocalNet dispenser and serves Streamable HTTP (/mcp) on port 9201.

How to run:
    python localnet/quickstart_server.py

What it prints:
    pay_to: <44-character Algorand address>
"""
import sys
from pathlib import Path

# Add current directory to path so _localnet can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn
from fastmcp import FastMCP
from ai_economy_sdk import DefaultAvmSigner, PaymentGate
from _localnet import ALGOD, new_funded_account

SERVER_PORT = 9201
TOOL_PRICE_MICROALGO = 5000


def main() -> None:
    server_sk, server_addr = new_funded_account(algos=10)
    print(f"pay_to: {server_addr}", flush=True)

    mcp = FastMCP("QuickstartServer")

    @mcp.tool()
    def echo(text: str) -> str:
        """Echo back input text."""
        return f"echo: {text}"

    gate = PaymentGate(
        signer=DefaultAvmSigner(server_sk, algod_client=ALGOD),
        network="localnet",
        pay_to=server_addr,
        asset_id=0,
        prices={"echo": TOOL_PRICE_MICROALGO},
    )

    app = gate.wrap(mcp, transport="streamable-http")
    uvicorn.run(app, host="127.0.0.1", port=SERVER_PORT, log_level="warning")


if __name__ == "__main__":
    main()
