"""Paid MCP tool client tutorial.

Connects to the paid summarize tool on port 9231 via paid_mcp_session, pays the
x402 payment on Algorand LocalNet, and confirms the transaction via Indexer.

How to run:
    python localnet/paid_mcp_tool/client.py

Expected output:
    Calling summarize tool...
    Result: Algorand is a pure proof-of-stake blockchain. It achieves immediate finality without forks.
    Price paid: 3000 microALGO
    Confirmed TxID: <txid> (confirmed at round <round>)
"""
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_economy_sdk import AIEconomyError, paid_mcp_session
from algosdk.v2client import indexer

from _localnet import ALGOD, ALGOD_TOKEN, ALGOD_URL, INDEXER_URL, new_funded_account

INDEXER = indexer.IndexerClient("", INDEXER_URL)


async def main():
    print("Generating funded buyer account on LocalNet...")
    buyer_sk, buyer_addr = new_funded_account(algos=5)

    test_text = (
        "Algorand is a pure proof-of-stake blockchain. "
        "It achieves immediate finality without forks. "
        "Smart contracts run directly on the AVM with predictable micro-cent fees."
    )

    start_round = ALGOD.status()["last-round"]

    print("Opening paid MCP session to http://127.0.0.1:9231/mcp ...")
    async with paid_mcp_session(
        "http://127.0.0.1:9231/mcp", buyer_sk, "localnet", algod_url=ALGOD_URL, algod_token=ALGOD_TOKEN
    ) as session:
        print("Calling summarize tool...")
        res = await session.call_tool("summarize", {"text": test_text})

        print(f"Result: {res.content[0].text}")

    # Look up payment transaction on Indexer by buyer address
    # Give indexer up to 5 seconds to ingest
    found_txn = None
    for _ in range(10):
        time.sleep(0.5)
        resp = INDEXER.search_transactions(address=buyer_addr, txn_type="pay", min_round=start_round)
        txns = resp.get("transactions", [])
        if txns:
            found_txn = txns[0]
            break

    if not found_txn:
        raise RuntimeError(f"Payment transaction for {buyer_addr} not found in indexer")

    txid = found_txn["id"]
    price = found_txn["payment-transaction"]["amount"]
    confirmed_round = found_txn.get("confirmed-round")

    print(f"Price paid: {price} microALGO")
    print(f"Confirmed TxID: {txid} (confirmed at round {confirmed_round})")


if __name__ == "__main__":
    asyncio.run(main())
