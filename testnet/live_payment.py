"""Optional live TestNet payment execution for x402 on Algorand.

Performs a real payment on TestNet ONLY when explicit environment variables are set:
  TESTNET_BUYER_MNEMONIC: 25-word mnemonic for buyer account on TestNet
  TESTNET_SERVER_MNEMONIC: 25-word mnemonic for server / fee-payer account on TestNet

TestNet ALGO can be obtained for free from the official dispenser:
  https://lora.algokit.io/testnet/fund

If the environment variables are not set, this script prints instructions and
exits cleanly with status code 0.

How to run:
    python testnet/live_payment.py
"""

import os
import sys
from algosdk.v2client import algod

from x402.schemas import PaymentPayload, PaymentRequirements
from x402_algorand import ALGORAND_TESTNET_CAIP2, PayerAvmSigner, ServerAvmSigner
from x402_algorand.exact.client import ExactAvmScheme as ClientScheme
from x402_algorand.exact.facilitator import ExactAvmScheme as FacilitatorScheme

ALGOD_URL = "https://testnet-api.algonode.cloud"
AMOUNT_MICROALGO = 1000  # 0.001 ALGO


def main():
    buyer_mn = os.environ.get("TESTNET_BUYER_MNEMONIC")
    server_mn = os.environ.get("TESTNET_SERVER_MNEMONIC")

    if not buyer_mn or not server_mn:
        print("TestNet live payment example requires environment variables:")
        print("  TESTNET_BUYER_MNEMONIC: 25-word mnemonic for buyer account on TestNet")
        print("  TESTNET_SERVER_MNEMONIC: 25-word mnemonic for server account on TestNet")
        print()
        print("TestNet ALGO can be obtained for free from https://lora.algokit.io/testnet/fund.")
        print("Environment variables not set; skipping live on-chain payment.")
        sys.exit(0)

    print("Initializing TestNet clients and accounts...")
    client = algod.AlgodClient("", ALGOD_URL)

    buyer_signer = PayerAvmSigner.from_mnemonic(buyer_mn)
    server_signer = ServerAvmSigner.from_mnemonic(server_mn, client)
    buyer_addr, server_addr = buyer_signer.address, server_signer.address
    print(f"Buyer address:  {buyer_addr}")
    print(f"Server address: {server_addr}")

    client_scheme = ClientScheme(buyer_signer, algod_url=ALGOD_URL)
    facilitator_scheme = FacilitatorScheme(server_signer)

    requirements = PaymentRequirements(
        scheme="exact",
        network=ALGORAND_TESTNET_CAIP2,
        asset="0",
        amount=str(AMOUNT_MICROALGO),
        pay_to=server_addr,
        max_timeout_seconds=300,
        extra={"feePayer": server_addr},
    )

    print(f"\nConstructing payment for {AMOUNT_MICROALGO} microALGO...")
    inner_payload = client_scheme.create_payment_payload(requirements)
    payload = PaymentPayload(x402_version=2, payload=inner_payload, accepted=requirements)

    print("Verifying payment payload with facilitator...")
    verify_res = facilitator_scheme.verify(payload, requirements)
    if not verify_res.is_valid:
        print(f"Verification failed: {verify_res.invalid_reason}")
        sys.exit(1)

    print("Submitting and settling atomic group on TestNet...")
    settle_res = facilitator_scheme.settle(payload, requirements)
    if not settle_res.success:
        print(f"Settlement failed: {settle_res.error_reason}")
        sys.exit(1)

    txid = settle_res.transaction
    print(f"Confirmed transaction ID: {txid}")
    print(f"View in explorer: https://lora.algokit.io/testnet/transaction/{txid}")


if __name__ == "__main__":
    main()
