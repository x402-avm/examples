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
from x402.http.utils import decode_payment_signature_header
from x402_algorand import ServerAvmSigner, caip2_from_genesis_hash
from x402_algorand.exact.facilitator import ExactAvmScheme

from _localnet import ALGOD as algod_client, new_funded_account

PORT = 9221

server_signer = ServerAvmSigner.from_private_key(new_funded_account()[0], algod_client)
server_addr = server_signer.address
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
