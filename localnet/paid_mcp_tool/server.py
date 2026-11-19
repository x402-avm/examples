"""Paid MCP tool server tutorial.

Starts a FastMCP server offering a paid summarize tool, protected by PaymentGate
on port 9231 with dynamic length-based pricing (1,000 microALGO per 100 characters,
minimum 3,000 microALGO).

How to run:
    python server.py

Expected output:
    Server running on http://127.0.0.1:9231
"""
import sys
import uvicorn
from fastmcp import FastMCP
from algosdk import account, kmd, transaction
from algosdk.v2client import algod
from ai_economy_sdk import DefaultAvmSigner, PaymentGate

ALGOD = algod.AlgodClient("a" * 64, "http://localhost:4001")


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


def price_summarize(tool: str, args: dict, sender: str | None = None) -> int:
    """Calculate price based on text length: 1,000 microALGO per 100 chars, min 3,000."""
    if tool == "summarize":
        text = args.get("text", "")
        units = (len(text) + 99) // 100
        return max(3000, units * 1000)
    return 3000


def create_app():
    # Fund server account on LocalNet
    server_sk, server_addr = new_funded_account(algos=5)
    signer = DefaultAvmSigner(server_sk, algod_client=ALGOD)

    mcp = FastMCP("Summarizer")

    @mcp.tool()
    def summarize(text: str) -> str:
        """Summarize text by extracting the primary sentences."""
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        if len(sentences) <= 2:
            return text.strip()
        return sentences[0] + ". " + sentences[1] + "."

    gate = PaymentGate(
        signer=signer,
        network="localnet",
        pay_to=server_addr,
        asset_id=0,
        prices=price_summarize,
    )
    return gate.wrap(mcp)


if __name__ == "__main__":
    app = create_app()
    print("Server starting on http://127.0.0.1:9231 ...", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=9231, log_level="warning")
