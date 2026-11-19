"""Flask paywall: GET /weather costs 10,000 microALGO on LocalNet (port 9212).

Uses the synchronous x402 classes; the server is payee, fee payer and facilitator.

    python localnet/flask_paywall.py
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from flask import Flask, jsonify
from werkzeug.serving import run_simple
from x402 import x402FacilitatorSync, x402ResourceServerSync
from x402.http.middleware.flask import payment_middleware
from x402_algorand import ServerAvmSigner, caip2_from_genesis_hash
from x402_algorand.exact import register_exact_avm_facilitator, register_exact_avm_server

from _localnet import ALGOD, new_funded_account

network = caip2_from_genesis_hash(ALGOD.suggested_params().gh)
signer = ServerAvmSigner.from_private_key(new_funded_account()[0], ALGOD)

facilitator = x402FacilitatorSync()
register_exact_avm_facilitator(facilitator, signer, network)
server = x402ResourceServerSync(facilitator)
register_exact_avm_server(server)

routes = {"GET /weather": {"accepts": [{
    "scheme": "exact", "price": {"amount": "10000", "asset": "0"},
    "network": network, "pay_to": signer.address,
}]}}

app = Flask(__name__)
payment_middleware(app, routes, server)


@app.get("/weather")
def weather():
    return jsonify(city="Boston", temperature=68, network=network)


if __name__ == "__main__":
    print(f"Flask paywall on http://127.0.0.1:9212/weather, pay to {signer.address}")
    logging.getLogger("werkzeug").setLevel(logging.ERROR)  # quiet dev-server banner and access log
    run_simple("127.0.0.1", 9212, app)
