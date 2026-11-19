"""Pricing strategies in ai-economy-sdk: fixed per-tool, dynamic arguments, and bulk discounts.

Starts an in-process FastMCP server on port 9202 and exercises three calls from a
buyer account:
1. Fixed price from a tool dictionary (compute = 6,000 microALGO).
2. Dynamic price computed from call arguments (echo = 5,000 base + 100 per word).
3. Bulk discount (50% off) automatically applied once past usage exceeds 10,000 microALGO.

How to run:
    python localnet/pricing.py

What it prints:
    Call 1 (compute - fixed dict price): charge = 6000 microALGO, result = 42
    Call 2 (echo - dynamic price 5 words): charge = 5500 microALGO, result = echo: one two three four five
    Call 3 (compute - bulk discount 50%): charge = 3000 microALGO, result = 84
"""
import asyncio
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn
from fastmcp import FastMCP
from ai_economy_sdk import DefaultAvmSigner, PaymentGate, paid_mcp_session
from ai_economy_sdk.chain import ChainReader
from _localnet import ALGOD, INDEXER_URL, new_funded_account

SERVER_PORT = 9202
SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}/sse"

TOOL_PRICES = {"compute": 6000}


def get_price(tool: str, args: dict[str, Any], sender: str | None) -> int:
    """Determine price based on tool name, arguments, and sender address."""
    if tool in TOOL_PRICES:
        return TOOL_PRICES[tool]
    if tool == "echo":
        words = len(args.get("text", "").split())
        return 5000 + words * 100
    return 5000


def main() -> None:
    server_sk, server_addr = new_funded_account(algos=10)
    buyer_sk, buyer_addr = new_funded_account(algos=10)

    mcp = FastMCP("PricingServer")

    @mcp.tool()
    def compute(n: int) -> int:
        """Double the input number."""
        return n * 2

    @mcp.tool()
    def echo(text: str) -> str:
        """Echo text back to the caller."""
        return f"echo: {text}"

    gate = PaymentGate(
        signer=DefaultAvmSigner(server_sk, algod_client=ALGOD),
        network="localnet",
        pay_to=server_addr,
        asset_id=0,
        prices=get_price,
        chain=ChainReader(INDEXER_URL),
        bulk_threshold=10_000,
        bulk_discount=0.5,
    )

    app = gate.wrap(mcp)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=SERVER_PORT, log_level="warning"))
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    # Wait for server to bind port
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", SERVER_PORT), 0.2).close()
            break
        except OSError:
            time.sleep(0.1)

    async def execute_client_calls() -> None:
        # Call 1: compute (fixed price: 6,000 microALGO)
        b0 = ALGOD.account_info(buyer_addr)["amount"]
        async with paid_mcp_session(SERVER_URL, buyer_sk, "localnet") as session:
            res1 = await session.call_tool("compute", {"n": 21})
        b1 = ALGOD.account_info(buyer_addr)["amount"]
        charge1 = b0 - b1
        print(f"Call 1 (compute - fixed dict price): charge = {charge1} microALGO, result = {res1.content[0].text}")

        # Call 2: echo with 5 words (dynamic price: 5,000 + 500 = 5,500 microALGO)
        async with paid_mcp_session(SERVER_URL, buyer_sk, "localnet") as session:
            res2 = await session.call_tool("echo", {"text": "one two three four five"})
        b2 = ALGOD.account_info(buyer_addr)["amount"]
        charge2 = b1 - b2
        print(f"Call 2 (echo - dynamic price 5 words): charge = {charge2} microALGO, result = {res2.content[0].text}")

        # Allow indexer to index preceding payments so cumulative usage exceeds 10,000 microALGO
        time.sleep(1.0)

        # Call 3: compute with bulk discount (6,000 * 0.5 = 3,000 microALGO)
        async with paid_mcp_session(SERVER_URL, buyer_sk, "localnet") as session:
            res3 = await session.call_tool("compute", {"n": 42})
        b3 = ALGOD.account_info(buyer_addr)["amount"]
        charge3 = b2 - b3
        print(f"Call 3 (compute - bulk discount 50%): charge = {charge3} microALGO, result = {res3.content[0].text}")

    try:
        asyncio.run(execute_client_calls())
    finally:
        server.should_exit = True
        server_thread.join(timeout=5)


if __name__ == "__main__":
    main()
