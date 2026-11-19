"""Paid MCP tool server tutorial.

Starts a FastMCP server offering a paid summarize tool, protected by PaymentGate
on port 9231 with dynamic length-based pricing (1,000 microALGO per 100 characters,
minimum 3,000 microALGO).

How to run:
    python localnet/paid_mcp_tool/server.py

Expected output:
    Server starting on http://127.0.0.1:9231/mcp
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import uvicorn
from ai_economy_sdk import DefaultAvmSigner, PaymentGate
from fastmcp import FastMCP

from _localnet import ALGOD, new_funded_account


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
    return gate.wrap(mcp, transport="streamable-http")


if __name__ == "__main__":
    app = create_app()
    print("Server starting on http://127.0.0.1:9231/mcp ...", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=9231, log_level="warning")
