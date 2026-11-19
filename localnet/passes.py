"""Passes in ai-economy-sdk: grant free tool access via on-chain receipt notes.

Demonstrates vendor-scoped passes on port 9203:
1. Buyer calls 'echo' without a pass, paying the standard 5,000 microALGO fee.
2. Buyer buys a pass by sending an on-chain payment with note 'x402-pass:<scope>' to the vendor.
3. Buyer calls 'echo' again; the server's PaymentGate verifies the active pass via the indexer and charges 0 microALGO.

How to run:
    python localnet/passes.py

What it prints:
    Call 1 (without pass): charge = 5000 microALGO, result = echo: without pass
    Bought pass on-chain (txid: ...)
    Call 2 (with pass): charge = 0 microALGO, result = echo: with pass
"""
import asyncio
import socket
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import algosdk.atomic_transaction_composer
import algosdk.transaction
import uvicorn
from fastmcp import FastMCP
from ai_economy_sdk import DefaultAvmSigner, PaymentGate, paid_mcp_session
from ai_economy_sdk.chain import ChainReader
from _localnet import ALGOD, INDEXER_URL, new_funded_account

SERVER_PORT = 9203
SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}/mcp"
SCOPE = "listing:echo-1"
PASS_PRICE = 50_000
TOOL_PRICE = 5_000


def main() -> None:
    server_sk, server_addr = new_funded_account(algos=10)
    buyer_sk, buyer_addr = new_funded_account(algos=10)

    mcp = FastMCP("PassServer")

    @mcp.tool()
    def echo(text: str) -> str:
        """Echo text back to the caller."""
        return f"echo: {text}"

    gate = PaymentGate(
        signer=DefaultAvmSigner(server_sk, algod_client=ALGOD),
        network="localnet",
        pay_to=server_addr,
        asset_id=0,
        prices={"echo": TOOL_PRICE},
        chain=ChainReader(INDEXER_URL),
        pass_scopes={SCOPE: PASS_PRICE},
        pass_days=30.0,
    )

    app = gate.wrap(mcp, transport="streamable-http")
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=SERVER_PORT, log_level="warning"))
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", SERVER_PORT), 0.2).close()
            break
        except OSError:
            time.sleep(0.1)

    async def execute_client_calls() -> None:
        # 1. Call before acquiring pass
        b0 = ALGOD.account_info(buyer_addr)["amount"]
        async with paid_mcp_session(SERVER_URL, buyer_sk, "localnet") as session:
            res1 = await session.call_tool("echo", {"text": "without pass"})
        b1 = ALGOD.account_info(buyer_addr)["amount"]
        charge1 = b0 - b1
        print(f"Call 1 (without pass): charge = {charge1} microALGO, result = {res1.content[0].text}")

        # 2. Buy pass via on-chain payment with x402-pass:<scope> note
        sp = ALGOD.suggested_params()
        note = f"x402-pass:{SCOPE}".encode("utf-8")
        pass_txn = algosdk.transaction.PaymentTxn(buyer_addr, sp, server_addr, PASS_PRICE, note=note)
        signer = algosdk.atomic_transaction_composer.AccountTransactionSigner(buyer_sk)
        stxn = signer.sign_transactions([pass_txn], [0])[0]
        txid = ALGOD.send_transaction(stxn)
        algosdk.transaction.wait_for_confirmation(ALGOD, txid, 10)
        print(f"Bought pass on-chain (txid: {txid[:8]}...)")

        # Wait for indexer to detect the pass transaction
        reader = ChainReader(INDEXER_URL)
        for _ in range(20):
            time.sleep(0.5)
            active = reader.active_passes(buyer_addr, server_addr, 0, {SCOPE: PASS_PRICE})
            if active:
                break

        # 3. Call after pass is active
        b2 = ALGOD.account_info(buyer_addr)["amount"]
        async with paid_mcp_session(SERVER_URL, buyer_sk, "localnet") as session:
            res2 = await session.call_tool("echo", {"text": "with pass"})
        b3 = ALGOD.account_info(buyer_addr)["amount"]
        charge2 = b2 - b3
        print(f"Call 2 (with pass): charge = {charge2} microALGO, result = {res2.content[0].text}")

    try:
        asyncio.run(execute_client_calls())
    finally:
        server.should_exit = True
        server_thread.join(timeout=5)


if __name__ == "__main__":
    main()
