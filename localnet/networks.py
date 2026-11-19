"""Network resolution, public endpoints, and USDC asset configuration in ai-economy-sdk.

Inspects MainNet, TestNet, and LocalNet configurations:
- Resolves each network name to its canonical CAIP-2 identifier.
- Retrieves full base64 genesis hash using genesis_hash_for.
- Retrieves default algod and indexer endpoints (AlgoNode public infrastructure or LocalNet).
- Looks up the official Circle USDC ASA identifier (31566704 on MainNet, 10458941 on TestNet).

How to run:
    python localnet/networks.py

What it prints:
    A formatted ASCII table showing network parameters for mainnet, testnet, and localnet.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ai_economy_sdk.network import endpoints_for, genesis_hash_for, resolve_network, usdc_asset_id
from _localnet import ALGOD

NETWORKS = ["mainnet", "testnet", "localnet"]


def main() -> None:
    header = f"{'Network':<10} | {'CAIP-2 Identifier':<44} | {'Genesis Hash':<46} | {'USDC ID':<10} | {'Algod Endpoint':<35} | {'Indexer Endpoint':<35}"
    print(header)
    print("-" * len(header))

    for net in NETWORKS:
        caip2 = resolve_network(net, ALGOD if net == "localnet" else None)
        gh = genesis_hash_for(caip2)
        ep = endpoints_for(net)
        usdc = str(usdc_asset_id(net))
        print(f"{net:<10} | {caip2:<44} | {gh:<46} | {usdc:<10} | {ep.algod_url:<35} | {ep.indexer_url:<35}")


if __name__ == "__main__":
    main()
