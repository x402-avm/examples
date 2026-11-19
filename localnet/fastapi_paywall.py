"""FastAPI paywall: GET /weather costs 10,000 microALGO on LocalNet (port 9211).

The server is payee, fee payer and in-process facilitator, so the buyer pays exactly the price.

    python localnet/fastapi_paywall.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn
from fastapi import FastAPI
from x402 import x402Facilitator, x402ResourceServer
from x402.http.middleware.fastapi import payment_middleware
from x402_algorand import ServerAvmSigner, caip2_from_genesis_hash
from x402_algorand.exact import register_exact_avm_facilitator, register_exact_avm_server

from _localnet import ALGOD, new_funded_account

network = caip2_from_genesis_hash(ALGOD.suggested_params().gh)
signer = ServerAvmSigner.from_private_key(new_funded_account()[0], ALGOD)

facilitator = x402Facilitator()
register_exact_avm_facilitator(facilitator, signer, network)
server = x402ResourceServer(facilitator)
register_exact_avm_server(server)

routes = {"GET /weather": {"accepts": [{
    "scheme": "exact", "price": {"amount": "10000", "asset": "0"},
    "network": network, "pay_to": signer.address,
}]}}

app = FastAPI()
app.middleware("http")(payment_middleware(routes, server))


@app.get("/weather")
async def weather():
    return {"city": "Boston", "temperature": 68, "network": network}


if __name__ == "__main__":
    print(f"FastAPI paywall on http://127.0.0.1:9211/weather, pay to {signer.address}")
    uvicorn.run(app, host="127.0.0.1", port=9211, log_level="warning")
