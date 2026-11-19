"""Paid MCP tool client tutorial.

Connects to the paid summarize tool on port 9231 via paid_mcp_session, pays the
x402 payment on Algorand LocalNet, and confirms the transaction via Indexer.

How to run:
    python client.py

Expected output:
    Calling summarize tool...
    Result: Algorand is a pure proof-of-stake blockchain. It achieves immediate finality without forks.
    Price paid: 3000 microALGO
    Confirmed TxID: <txid> (confirmed at round <round>)
"""
import asyncio
import time
from algosdk import account, kmd, transaction
from algosdk.v2client import algod, indexer
from ai_economy_sdk import paid_mcp_session

ALGOD = algod.AlgodClient("a" * 64, "http://localhost:4001")
INDEXER = indexer.IndexerClient("", "http://localhost:8980")


def dispenser():
    """Retrieve LocalNet dispenser account from KMD."""
    k = kmd.KMDClient("a" * 64, "http://localhost:4002")
    w = next(x for x in k.list_wallets() if x["name"] == "unencrypted-default-wallet")
    h = k.init_wallet_handle(w["id"], "")
    addr = max(k.list_keys(h), key=lambda a: ALGOD.account_info(a)["amount"])
    return addr, k.export_key(h, "", addr)


def new_funded_account(algos=10):
    """Generate a new account funded from the LocalNet dispenser."""
    sk, addr = account.generate_account()
    d_addr, d_sk = dispenser()
    sp = ALGOD.suggested_params()
    txn = transaction.PaymentTxn(d_addr, sp, addr, algos * 1_000_000)
    ALGOD.send_transaction(txn.sign(d_sk))
    transaction.wait_for_confirmation(ALGOD, txn.get_txid(), 10)
    return sk, addr


async def main():
    print("Generating funded buyer account on LocalNet...")
    buyer_sk, buyer_addr = new_funded_account(algos=5)

    test_text = (
        "Algorand is a pure proof-of-stake blockchain. "
        "It achieves immediate finality without forks. "
        "Smart contracts run directly on the AVM with predictable micro-cent fees."
    )

    start_round = ALGOD.status()["last-round"]

    print("Opening paid MCP session to http://127.0.0.1:9231/sse ...")
    async with paid_mcp_session(
        sse_url="http://127.0.0.1:9231/sse",
        private_key=buyer_sk,
        network="localnet",
        algod_url="http://localhost:4001",
        algod_token="a" * 64,
    ) as session:
        print("Calling summarize tool...")
        res = await session.call_tool("summarize", {"text": test_text})

        summary_text = ""
        for content in res.content:
            if hasattr(content, "text"):
                summary_text += content.text
            elif isinstance(content, dict) and "text" in content:
                summary_text += content["text"]
            else:
                summary_text += str(content)

        print(f"Result: {summary_text.strip()}")

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
