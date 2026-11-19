"""Browser paywall tutorial server.

Serves a static web page and protects a premium endpoint (/api/premium)
using x402 payment middleware on port 9232 (4,000 microALGO per request).

How to run:
    python server.py

Expected output:
    Server running on http://127.0.0.1:9232
"""
from pathlib import Path
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from algosdk import account, kmd, transaction
from algosdk.v2client import algod
from x402 import x402ResourceServer, x402Facilitator
from x402_algorand.exact.register import register_exact_avm_server, register_exact_avm_facilitator
from x402.http import x402HTTPResourceServer, HTTPRequestContext
from x402.http.middleware.fastapi import FastAPIAdapter
from ai_economy_sdk import DefaultAvmSigner, resolve_network

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


def create_app():
    network = resolve_network("localnet", ALGOD)

    # Fund server account on LocalNet
    server_sk, server_addr = new_funded_account(algos=5)
    signer = DefaultAvmSigner(server_sk, algod_client=ALGOD)

    facilitator = x402Facilitator()
    register_exact_avm_facilitator(facilitator, signer, network)

    server = x402ResourceServer(facilitator_clients=facilitator)
    register_exact_avm_server(server)

    routes = {
        "GET /api/premium": {
            "accepts": [
                {
                    "scheme": "exact",
                    "pay_to": server_addr,
                    "price": {"amount": "4000", "asset": "0"},
                    "network": network,
                }
            ],
            "description": "Deep sea exploration premium report",
        }
    }

    http_server = x402HTTPResourceServer(server, routes)
    http_server.initialize()

    app = FastAPI(title="Browser Paywall Tutorial")

    @app.middleware("http")
    async def x402_gate(request: Request, call_next):
        adapter = FastAPIAdapter(request)
        context = HTTPRequestContext(
            adapter=adapter,
            path=request.url.path,
            method=request.method,
            payment_header=(
                adapter.get_header("payment-signature") or adapter.get_header("x-payment")
            ),
        )

        if not http_server.requires_payment(context):
            return await call_next(request)

        result = await http_server.process_http_request(context)

        if result.type == "no-payment-required":
            return await call_next(request)

        if result.type == "payment-error":
            response = result.response
            if response is None:
                return JSONResponse(content={"error": "Payment required"}, status_code=402)
            return JSONResponse(
                content=response.body or {},
                status_code=response.status,
                headers=response.headers,
            )

        if result.type == "payment-verified":
            settle_result = await http_server.process_settlement(
                result.payment_payload,
                result.payment_requirements,
            )
            if not settle_result.success:
                return JSONResponse(
                    content={
                        "error": "Settlement failed",
                        "details": settle_result.error_reason,
                    },
                    status_code=402,
                )

            # Proceed to protected route
            response = await call_next(request)
            for k, v in settle_result.headers.items():
                response.headers[k] = v
            return response

        return await call_next(request)

    @app.get("/api/premium")
    def get_premium():
        return {
            "title": "Deep Sea Hydrothermal Vent Survey",
            "findings": "Dense polymetallic sulfides discovered at depth 2,400m.",
            "status": "unlocked",
        }

    # Mount static assets directory
    static_dir = Path(__file__).parent.resolve()
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app


if __name__ == "__main__":
    app = create_app()
    print("Server starting on http://127.0.0.1:9232 ...", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=9232, log_level="warning")
