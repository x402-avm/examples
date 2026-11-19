"""Public network simulation for x402 Algorand payments on TestNet.

Performs read-only validation against real TestNet ledger without spending funds:
1. Queries the public AlgoNode indexer to identify real funded accounts holding USDC and ALGO.
2. Constructs payment groups for ALGO (asset 0) and USDC (asset 10458941), both with and without fee payers.
3. Evaluates the constructed atomic groups via Algod's simulate endpoint using empty signatures.
4. Confirms that all 4 test cases simulate successfully without on-chain execution.

How to run:
    python testnet/simulate.py

What it prints:
    Network progress and "ok" for each of the 4 test cases.
"""

import httpx
from algosdk import encoding, transaction
from algosdk.v2client import algod
from algosdk.v2client.models import SimulateRequest, SimulateRequestTransactionGroup

from x402.schemas import PaymentRequirements
from x402_algorand.constants import ALGORAND_TESTNET_CAIP2
from x402_algorand.exact.client import ExactAvmScheme as ExactAvmClient

CONFIG = {
    "name": "testnet",
    "caip": ALGORAND_TESTNET_CAIP2,
    "algod_url": "https://testnet-api.algonode.cloud",
    "indexer_url": "https://testnet-idx.algonode.cloud",
    "usdc_id": 10458941,
}


class _WatchOnly:
    """Watch-only signer providing an address without private keys.

    Generates unsigned transactions for simulate endpoint evaluation.
    """

    def __init__(self, address: str):
        self.address = address

    def sign_transactions(self, txns: list[bytes], indexes: list[int]) -> list[None]:
        return [None] * len(txns)


def get_algod(cfg: dict) -> algod.AlgodClient:
    return algod.AlgodClient("", cfg["algod_url"])


def find_funded_holders(cfg: dict, n: int = 3) -> list[str]:
    """Find real funded accounts holding ALGO and USDC via public indexer."""
    client = get_algod(cfg)
    idx_url = cfg["indexer_url"]
    usdc_id = cfg["usdc_id"]

    resp = httpx.get(
        f"{idx_url}/v2/assets/{usdc_id}/balances",
        params={"currency-greater-than": 5_000_000, "limit": 40},
        timeout=20,
    )
    balances = resp.json().get("balances", [])
    out = []
    for b in balances:
        try:
            info = client.account_info(b["address"])
            if info["amount"] - info["min-balance"] > 2_000_000 and not info.get("auth-addr"):
                out.append(b["address"])
                if len(out) == n:
                    return out
        except Exception:
            continue
    raise RuntimeError(f"Could not find {n} funded USDC holders on {cfg['name']}")


def simulate_group(client: algod.AlgodClient, group_b64: list[str]) -> str | None:
    """Run transaction group through Algod simulation with empty signatures."""
    stx = []
    for b in group_b64:
        d = encoding.msgpack_decode(b)
        stx.append(
            d
            if isinstance(d, transaction.SignedTransaction)
            else transaction.SignedTransaction(d, None)
        )
    req = SimulateRequest(
        txn_groups=[SimulateRequestTransactionGroup(txns=stx)],
        allow_empty_signatures=True,
    )
    res = client.simulate_transactions(req)
    return res["txn-groups"][0].get("failure-message")


def main():
    net_name = CONFIG["name"]
    caip = CONFIG["caip"]
    print(f"Testing {net_name} ({caip})...")

    holders = find_funded_holders(CONFIG, n=3)
    payer, pay_to, fp = holders
    client = get_algod(CONFIG)

    test_cases = [
        ("ALGO", "0", True),
        ("ALGO", "0", False),
        ("USDC", str(CONFIG["usdc_id"]), True),
        ("USDC", str(CONFIG["usdc_id"]), False),
    ]

    for asset_name, asset_id, fee_payer in test_cases:
        extra = {"feePayer": fp} if fee_payer else {}
        req = PaymentRequirements(
            scheme="exact",
            network=caip,
            asset=asset_id,
            amount="10000",
            pay_to=pay_to,
            max_timeout_seconds=300,
            extra=extra,
        )

        avm_client = ExactAvmClient(_WatchOnly(payer), algod_url=CONFIG["algod_url"])
        payload = avm_client.create_payment_payload(req)
        failure = simulate_group(client, payload["paymentGroup"])
        assert failure is None, f"Simulation failed on {net_name} {asset_name} (fee_payer={fee_payer}): {failure}"
        print(f"  {net_name} {asset_name} (fee_payer={fee_payer}): ok")

    print(f"All {net_name} simulations passed successfully.")


if __name__ == "__main__":
    main()
