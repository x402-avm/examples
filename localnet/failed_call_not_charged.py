"""Settle-on-success guarantee: failed tool calls are never charged on-chain.

Starts an in-process FastMCP server on port 9204 with a tool that raises an exception.
A buyer calls the tool via paid_mcp_session and receives an error result, but
PaymentGate intercepts the failure and does not submit the signed payment to the
network. The buyer balance remains completely unchanged.

How to run:
    python localnet/failed_call_not_charged.py

What it prints:
    Tool call returned (isError=True): ...
    Balance drop: 0 microALGO
"""
import asyncio
import socket
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn
from fastmcp import FastMCP
from ai_economy_sdk import DefaultAvmSigner, PaymentGate, paid_mcp_session
from _localnet import ALGOD, new_funded_account

SERVER_PORT = 9204
SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}/mcp"
PRICE = 5000


def main() -> None:
    server_sk, server_addr = new_funded_account(algos=10)
    buyer_sk, buyer_addr = new_funded_account(algos=10)

    mcp = FastMCP("FailServer")

    @mcp.tool()
    def fail_tool(reason: str) -> str:
        """Simulate a tool raising an unexpected error."""
        raise RuntimeError(f"Deliberate tool failure: {reason}")

    gate = PaymentGate(
        signer=DefaultAvmSigner(server_sk, algod_client=ALGOD),
        network="localnet",
        pay_to=server_addr,
        asset_id=0,
        prices={"fail_tool": PRICE},
    )

    app = gate.wrap(mcp, transport="streamable-http")
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=SERVER_PORT, log_level="error"))
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", SERVER_PORT), 0.2).close()
            break
        except OSError:
            time.sleep(0.1)

    async def execute_failing_call() -> None:
        b_before = ALGOD.account_info(buyer_addr)["amount"]

        async with paid_mcp_session(SERVER_URL, buyer_sk, "localnet") as session:
            result = await session.call_tool("fail_tool", {"reason": "computation error"})
            is_err = getattr(result, "isError", False)
            err_msg = result.content[0].text if result.content else "no content"
            print(f"Tool call returned (isError={is_err}): {err_msg}")

        b_after = ALGOD.account_info(buyer_addr)["amount"]
        drop = b_before - b_after
        print(f"Balance drop: {drop} microALGO")

    try:
        asyncio.run(execute_failing_call())
    finally:
        server.should_exit = True
        server_thread.join(timeout=5)


if __name__ == "__main__":
    main()
