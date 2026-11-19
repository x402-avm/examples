"""Tiny FastAPI x402 paywall server on LocalNet for JavaScript client tests.

Demonstrates:
1. Serving an x402 paywalled HTTP endpoint on port 9221 requiring 5,000 microALGO.
2. Generating standard x402 v2 402 PAYMENT-REQUIRED challenge headers for LocalNet.
3. Verifying and settling client-submitted payment groups on-chain using ExactAvmScheme.

How to run:
    python localnet/server_for_js.py

What it prints:
    Server startup logs and transaction settlement confirmations on port 9221.
"""

import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn
from fastapi import FastAPI, Request, Response
from algosdk import kmd
from algosdk.v2client import algod
from ai_economy_sdk import DefaultAvmSigner
from x402_algorand.exact.facilitator import ExactAvmScheme
from x402_algorand import caip2_from_genesis_hash
from x402.http.utils import decode_payment_signature_header

ALGOD_URL = "http://localhost:4001"
ALGOD_TOKEN = "a" * 64
KMD_URL = "http://localhost:4002"
KMD_TOKEN = "a" * 64
PORT = 9221

algod_client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_URL)


def get_server_dispenser_account() -> tuple[str, str]:
    """Retrieve LocalNet default wallet dispenser account."""
    k = kmd.KMDClient(KMD_TOKEN, KMD_URL)
    wallets = k.list_wallets()
    w = next(x for x in wallets if x["name"] == "unencrypted-default-wallet")
    handle = k.init_wallet_handle(w["id"], "")
    keys = k.list_keys(handle)
    addr = max(keys, key=lambda a: algod_client.account_info(a)["amount"])
    sk = k.export_key(handle, "", addr)
    return addr, sk


server_addr, server_sk = get_server_dispenser_account()
server_signer = DefaultAvmSigner(server_sk, algod_client=algod_client)
facilitator = ExactAvmScheme(server_signer)

app = FastAPI(title="x402-avm-js Test Paywall Server")


@app.get("/health")
def health():
    return {"status": "ok", "server_address": server_addr}


@app.get("/paid")
async def paid_endpoint(request: Request):
    sp = algod_client.suggested_params()
    genesis_hash_b64 = sp.gh if isinstance(sp.gh, str) else base64.b64encode(sp.gh).decode("utf-8")
    network = caip2_from_genesis_hash(genesis_hash_b64)

    sig_header = request.headers.get("payment-signature")
    if not sig_header:
        req = {
            "scheme": "exact",
            "network": network,
            "asset": "0",
            "amount": "5000",
            "payTo": server_addr,
            "maxTimeoutSeconds": 300,
            "extra": {
                "feePayer": server_addr,
                "decimals": 6,
                "genesisHash": genesis_hash_b64,
                "genesisId": sp.gen,
            },
        }
        challenge = {
            "x402Version": 2,
            "error": "Payment required",
            "resource": {
                "url": str(request.url),
                "description": "5000 microALGO premium resource",
                "mimeType": "application/json",
            },
            "accepts": [req],
        }
        b64_challenge = base64.b64encode(json.dumps(challenge).encode("utf-8")).decode("utf-8")
        return Response(
            content=json.dumps({"error": "Payment required"}),
            status_code=402,
            headers={
                "PAYMENT-REQUIRED": b64_challenge,
                "Content-Type": "application/json",
            },
        )

    # Decode and verify submitted payment
    payload = decode_payment_signature_header(sig_header)
    verify_res = facilitator.verify(payload, payload.accepted)
    if not verify_res.is_valid:
        return Response(
            content=json.dumps({"error": verify_res.invalid_reason or "Verification failed"}),
            status_code=400,
            headers={"Content-Type": "application/json"},
        )

    # Settle payment on-chain
    settle_res = facilitator.settle(payload, payload.accepted)
    if not settle_res.success:
        return Response(
            content=json.dumps({"error": settle_res.error_reason or "Settlement failed"}),
            status_code=400,
            headers={"Content-Type": "application/json"},
        )

    resp_payload = {
        "status": "ok",
        "data": "Access granted to premium resource",
        "txid": settle_res.transaction,
        "payer": verify_res.payer,
    }
    resp_header = base64.b64encode(
        json.dumps({
            "success": True,
            "transaction": settle_res.transaction,
            "network": network,
        }).encode("utf-8")
    ).decode("utf-8")

    return Response(
        content=json.dumps(resp_payload),
        status_code=200,
        headers={
            "Content-Type": "application/json",
            "PAYMENT-RESPONSE": resp_header,
        },
    )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="info")
