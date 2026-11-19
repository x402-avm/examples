"""Manual x402 payment flow without web frameworks on Algorand LocalNet.

Demonstrates the direct AVM payment scheme lifecycle:
1. Generates and funds client and server accounts from the LocalNet KMD dispenser.
2. Builds PaymentRequirements for a 10,000 microALGO payment with server as fee payer.
3. Client creates and signs the payment payload using ExactAvmScheme (client).
4. Facilitator verifies the payment group and simulation using ExactAvmScheme (facilitator).
5. Facilitator settles the atomic group on-chain and waits for confirmation.
6. Prints the transaction ID and the confirmed block round.

How to run:
    python localnet/manual_flow.py

What it prints:
    Client and server addresses, verification status, settled transaction ID,
    and confirmed block round.
"""

import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from algosdk import account, encoding, kmd, transaction
from algosdk.v2client import algod
from algosdk.v2client.models import SimulateRequest, SimulateRequestTransactionGroup

from x402.schemas import PaymentPayload, PaymentRequirements
from x402_algorand.exact.client import ExactAvmScheme as ClientScheme
from x402_algorand.exact.facilitator import ExactAvmScheme as FacilitatorScheme
from x402_algorand.utils import caip2_from_genesis_hash

ALGOD_URL = "http://localhost:4001"
ALGOD_TOKEN = "a" * 64
algod_client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_URL)

sp = algod_client.suggested_params()
network = caip2_from_genesis_hash(sp.gh)


# 1. LocalNet dispenser helper
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


# 2. Signer implementations
class ManualAvmSigner:
    """AVM signer supporting client signing and facilitator execution."""

    def __init__(self, private_key: str, client: algod.AlgodClient):
        self.private_key = private_key
        self.address = account.address_from_private_key(private_key)
        self.client = client

    def get_addresses(self) -> list[str]:
        return [self.address]

    def sign_transactions(self, unsigned_txns: list[bytes], indexes: list[int]) -> list[bytes | None]:
        signed = []
        for i, txn_bytes in enumerate(unsigned_txns):
            if i in indexes:
                signed.append(self._sign_raw(txn_bytes))
            else:
                signed.append(None)
        return signed

    def sign_transaction(self, txn_bytes: bytes, fee_payer: str, network: str) -> bytes:
        return self._sign_raw(txn_bytes)

    def sign_group(self, group_bytes: list[bytes], fee_payer: str, indexes: list[int], network: str) -> list[bytes]:
        signed = list(group_bytes)
        for i in indexes:
            signed[i] = self._sign_raw(group_bytes[i])
        return signed

    def simulate_group(self, group_bytes: list[bytes], network: str):
        decoded = [self._decode(b) for b in group_bytes]
        req = SimulateRequest(
            txn_groups=[SimulateRequestTransactionGroup(txns=decoded)],
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
        return encoding.msgpack_decode(base64.b64encode(raw_bytes).decode())

    def _sign_raw(self, txn_bytes: bytes) -> bytes:
        txn = self._decode(txn_bytes)
        return base64.b64decode(encoding.msgpack_encode(txn.sign(self.private_key)))


def main():
    # Setup accounts
    server_sk, server_addr = new_funded_account(10)
    client_sk, client_addr = new_funded_account(10)
    print(f"Server address: {server_addr}")
    print(f"Client address: {client_addr}")
    print(f"Network: {network}")

    server_signer = ManualAvmSigner(server_sk, algod_client)
    client_signer = ManualAvmSigner(client_sk, algod_client)

    client_scheme = ClientScheme(client_signer, algod_url=ALGOD_URL, algod_token=ALGOD_TOKEN)
    facilitator_scheme = FacilitatorScheme(server_signer)

    # 1. Server defines payment requirements
    requirements = PaymentRequirements(
        scheme="exact",
        network=network,
        asset="0",
        amount="10000",
        pay_to=server_addr,
        max_timeout_seconds=300,
        extra={"feePayer": server_addr},
    )

    # 2. Client constructs payment payload
    inner_payload = client_scheme.create_payment_payload(requirements)
    payload = PaymentPayload(x402_version=2, payload=inner_payload, accepted=requirements)

    # 3. Facilitator verifies payment
    verify_result = facilitator_scheme.verify(payload, requirements)
    assert verify_result.is_valid, f"Verification failed: {verify_result.invalid_reason}"
    print(f"Verification successful: Valid payment from {verify_result.payer}")

    # 4. Facilitator settles transaction group on-chain
    settle_result = facilitator_scheme.settle(payload, requirements)
    assert settle_result.success, f"Settlement failed: {settle_result.error_reason}"
    print(f"Settled transaction ID: {settle_result.transaction}")

    # 5. Check confirmation details
    info = algod_client.pending_transaction_info(settle_result.transaction)
    confirmed_round = info.get("confirmed-round")
    print(f"Confirmed round: {confirmed_round}")
    assert confirmed_round and confirmed_round > 0, "Transaction was not confirmed"
    print("Manual payment flow completed successfully.")


if __name__ == "__main__":
    main()
