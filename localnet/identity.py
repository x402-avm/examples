"""Identity proof verification via zero-fee self-signed Algorand transactions.

Demonstrates sign_identity_txn and verify_identity_txn:
1. Generates an account and constructs an X-Identity-Txn header bound to the network genesis hash.
2. Verifies the header on the receiver side, asserting the recovered address matches the signer.
3. Proves that verifying with a mismatched genesis hash rejects the signature (returns None).

How to run:
    python localnet/identity.py

What it prints:
    Address: <44-character Algorand address>
    Verified address matches: True
    Wrong genesis hash rejected: True
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from algosdk import account
from ai_economy_sdk import sign_identity_txn, verify_identity_txn
from _localnet import ALGOD

WRONG_GENESIS_HASH = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="


def main() -> None:
    sk, addr = account.generate_account()
    print(f"Address: {addr}")

    # Read current LocalNet genesis hash
    sp = ALGOD.suggested_params()
    current_gh = sp.gh

    # 1. Sign identity proof for the current network
    headers = sign_identity_txn(sk, current_gh)

    # 2. Verify with matching genesis hash
    verified_address = verify_identity_txn(headers["X-Identity-Txn"], current_gh)
    matches = verified_address == addr
    print(f"Verified address matches: {matches}")

    # 3. Attempt verification with mismatched genesis hash
    rejected = verify_identity_txn(headers["X-Identity-Txn"], WRONG_GENESIS_HASH)
    print(f"Wrong genesis hash rejected: {rejected is None}")


if __name__ == "__main__":
    main()
