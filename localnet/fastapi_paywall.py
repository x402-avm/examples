"""FastAPI payment wall example for x402 on Algorand LocalNet.

Protects a GET /weather endpoint requiring a 10,000 microALGO (asset 0) payment.
The server acts as both the resource server and the in-process facilitator, sponsoring
transaction fees so the buyer pays exactly 10,000 microALGO with zero network fee.

How to run:
    python localnet/fastapi_paywall.py

What it prints:
    Server initialization messages, funded server address, network CAIP-2 ID,
    and uvicorn startup listening on http://127.0.0.1:9211.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn
from fastapi import FastAPI
from algosdk import account, kmd, transaction
from algosdk.v2client import algod

from x402 import x402Facilitator, x402ResourceServer
from x402.http.middleware.fastapi import payment_middleware
from x402_algorand.exact.register import (
    register_exact_avm_server,
    register_exact_avm_facilitator,
)
from x402_algorand.utils import caip2_from_genesis_hash

# 1. Connect to LocalNet Algod
ALGOD_URL = "http://localhost:4001"
ALGOD_TOKEN = "a" * 64
algod_client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_URL)

# Derive CAIP-2 network identifier from LocalNet genesis hash
sp = algod_client.suggested_params()
network = caip2_from_genesis_hash(sp.gh)


# 2. LocalNet dispenser helper to fund server account
def dispenser():
    k = kmd.KMDClient(ALGOD_TOKEN, "http://localhost:4002")
    w = next(x for x in k.list_wallets() if x["name"] == "unencrypted-default-wallet")
    h = k.init_wallet_handle(w["id"], "")
    addr = max(k.list_keys(h), key=lambda a: algod_client.account_info(a)["amount"])
    return addr, k.export_key(h, "", addr)


def new_funded_account(algos: int = 10):
    sk, addr = account.generate_account()
    d_addr, d_sk = dispenser()
    txn = transaction.PaymentTxn(d_addr, algod_client.suggested_params(), addr, algos * 1_000_000)
    algod_client.send_transaction(txn.sign(d_sk))
    transaction.wait_for_confirmation(algod_client, txn.get_txid(), 10)
    return sk, addr


# 3. Server signer implementation
class ServerAvmSigner:
    """Server-side AVM signer for fee payment, simulation, and settlement."""

    def __init__(self, private_key: str, client: algod.AlgodClient):
        import base64
        from algosdk import encoding
        from algosdk.v2client.models import SimulateRequest, SimulateRequestTransactionGroup

        self.private_key = private_key
        self.address = account.address_from_private_key(private_key)
        self.client = client
        self._encoding = encoding
        self._b64 = base64
        self._SimulateRequest = SimulateRequest
        self._SimulateRequestTransactionGroup = SimulateRequestTransactionGroup

    def get_addresses(self) -> list[str]:
        return [self.address]

    def sign_transaction(self, txn_bytes: bytes, fee_payer: str, network: str) -> bytes:
        return self._sign_raw(txn_bytes)

    def sign_group(self, group_bytes: list[bytes], fee_payer: str, indexes: list[int], network: str) -> list[bytes]:
        signed = list(group_bytes)
        for i in indexes:
            signed[i] = self._sign_raw(group_bytes[i])
        return signed

    def simulate_group(self, group_bytes: list[bytes], network: str):
        decoded = [self._decode(b) for b in group_bytes]
        req = self._SimulateRequest(
            txn_groups=[self._SimulateRequestTransactionGroup(txns=decoded)],
            allow_empty_signatures=True,
        )
        result = self.client.simulate_transactions(req)
        txn_groups = result.get("txn-groups", [])
        if txn_groups and txn_groups[0].get("failure-message"):
            raise RuntimeError(txn_groups[0]["failure-message"])
        return result

    def send_group(self, group_bytes: list[bytes], network: str) -> str:
        decoded = [self._decode(b) for b in group_bytes]
        return self.client.send_transactions(decoded)

    def confirm_transaction(self, txid: str, network: str, rounds: int = 4):
        return transaction.wait_for_confirmation(self.client, txid, rounds)

    def _decode(self, raw_bytes: bytes):
        return self._encoding.msgpack_decode(self._b64.b64encode(raw_bytes).decode())

    def _sign_raw(self, txn_bytes: bytes) -> bytes:
        txn = self._decode(txn_bytes)
        return self._b64.b64decode(self._encoding.msgpack_encode(txn.sign(self.private_key)))


# Initialize funded server account
server_sk, server_addr = new_funded_account(10)
server_signer = ServerAvmSigner(server_sk, algod_client)

# 4. Set up x402 Facilitator and Resource Server
facilitator = x402Facilitator()
register_exact_avm_facilitator(facilitator, server_signer, network)

resource_server = x402ResourceServer(facilitator)
register_exact_avm_server(resource_server)

# 5. Define FastAPI application with payment middleware
app = FastAPI(title="x402 Algorand Weather Paywall")

routes = {
    "GET /weather": {
        "accepts": [
            {
                "scheme": "exact",
                "price": {"amount": "10000", "asset": "0"},
                "network": network,
                "pay_to": server_addr,
            }
        ]
    }
}

app.middleware("http")(payment_middleware(routes, resource_server))


@app.get("/weather")
async def get_weather():
    """Protected weather endpoint: returns current weather conditions."""
    return {
        "city": "Boston",
        "temperature": 68,
        "conditions": "sunny",
        "network": network,
    }


if __name__ == "__main__":
    print(f"Starting x402 FastAPI server on port 9211...")
    print(f"Server address: {server_addr}")
    print(f"Network: {network}")
    print(f"Endpoint: GET http://127.0.0.1:9211/weather (cost: 10,000 microALGO)")
    uvicorn.run(app, host="127.0.0.1", port=9211, log_level="warning")
