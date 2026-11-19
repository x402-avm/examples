"""The x402 exact-scheme lifecycle on LocalNet with no web framework.

Requirements -> client signs payload -> facilitator verifies -> facilitator settles on-chain.

    python localnet/manual_flow.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from x402.schemas import PaymentPayload, PaymentRequirements
from x402_algorand import PayerAvmSigner, ServerAvmSigner, caip2_from_genesis_hash
from x402_algorand.exact.client import ExactAvmScheme as ClientScheme
from x402_algorand.exact.facilitator import ExactAvmScheme as FacilitatorScheme

from _localnet import ALGOD, ALGOD_TOKEN, ALGOD_URL, new_funded_account

network = caip2_from_genesis_hash(ALGOD.suggested_params().gh)
server_sk, server_addr = new_funded_account()
client_sk, client_addr = new_funded_account()
print(f"server {server_addr}\nclient {client_addr}\nnetwork {network}")

client_scheme = ClientScheme(PayerAvmSigner.from_private_key(client_sk), algod_url=ALGOD_URL, algod_token=ALGOD_TOKEN)
facilitator = FacilitatorScheme(ServerAvmSigner.from_private_key(server_sk, ALGOD))

requirements = PaymentRequirements(
    scheme="exact", network=network, asset="0", amount="10000", pay_to=server_addr,
    max_timeout_seconds=300, extra={"feePayer": server_addr},
)
payload = PaymentPayload(
    x402_version=2, payload=client_scheme.create_payment_payload(requirements), accepted=requirements
)

verified = facilitator.verify(payload, requirements)
assert verified.is_valid, verified.invalid_reason
print(f"verified payment from {verified.payer}")

settled = facilitator.settle(payload, requirements)
assert settled.success, settled.error_reason
round_ = ALGOD.pending_transaction_info(settled.transaction)["confirmed-round"]
print(f"settled {settled.transaction} in round {round_}")
