"""Browser paywall server: serves the static page and charges 4,000 microALGO for /api/premium.

    python localnet/browser_paywall/server.py     # http://127.0.0.1:9232
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from x402 import x402Facilitator, x402ResourceServer
from x402.http.middleware.fastapi import payment_middleware
from x402_algorand import ServerAvmSigner, caip2_from_genesis_hash
from x402_algorand.exact import register_exact_avm_facilitator, register_exact_avm_server

from _localnet import ALGOD, new_funded_account


def create_app() -> FastAPI:
    network = caip2_from_genesis_hash(ALGOD.suggested_params().gh)
    signer = ServerAvmSigner.from_private_key(new_funded_account()[0], ALGOD)

    facilitator = x402Facilitator()
    register_exact_avm_facilitator(facilitator, signer, network)
    server = x402ResourceServer(facilitator)
    register_exact_avm_server(server)

    routes = {"GET /api/premium": {
        "accepts": [{"scheme": "exact", "pay_to": signer.address,
                     "price": {"amount": "4000", "asset": "0"}, "network": network}],
        "description": "Deep sea exploration premium report",
    }}

    app = FastAPI(title="Browser Paywall")
    app.middleware("http")(payment_middleware(routes, server))

    @app.get("/api/premium")
    def premium():
        return {
            "title": "Deep Sea Hydrothermal Vent Survey",
            "findings": "Dense polymetallic sulfides discovered at depth 2,400m.",
            "status": "unlocked",
        }

    app.mount("/", StaticFiles(directory=Path(__file__).parent, html=True), name="static")
    return app


if __name__ == "__main__":
    print("Browser paywall on http://127.0.0.1:9232", flush=True)
    uvicorn.run(create_app(), host="127.0.0.1", port=9232, log_level="warning")
