"""Paid MCP client session using ai-economy-sdk on Algorand LocalNet.

Funds a fresh buyer account via the LocalNet dispenser, establishes a paid MCP
session to http://127.0.0.1:9201/sse, calls the 'echo' tool, and verifies the on-chain
charge.

How to run:
    1. Start quickstart_server.py in the background
    2. python localnet/quickstart_client.py

What it prints:
    Result: echo: hello world
    Balance drop: 5000 microALGO
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ai_economy_sdk import paid_mcp_session
from _localnet import ALGOD, new_funded_account

SERVER_URL = "http://127.0.0.1:9201/sse"


async def main() -> None:
    buyer_sk, buyer_addr = new_funded_account(algos=5)
    before_balance = ALGOD.account_info(buyer_addr)["amount"]

    async with paid_mcp_session(SERVER_URL, buyer_sk, "localnet") as session:
        result = await session.call_tool("echo", {"text": "hello world"})
        output_text = result.content[0].text
        print(f"Result: {output_text}")

    after_balance = ALGOD.account_info(buyer_addr)["amount"]
    drop = before_balance - after_balance
    print(f"Balance drop: {drop} microALGO")


if __name__ == "__main__":
    asyncio.run(main())
