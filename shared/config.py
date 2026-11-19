"""Multi-network configuration manager for Algorand payments.

Switches configuration between LocalNet, TestNet, and MainNet using the
NETWORK environment variable. Selects ALGO for LocalNet development and
USDC for TestNet and MainNet.

Usage:
    NETWORK=localnet python shared/config.py
    NETWORK=testnet python shared/config.py
    NETWORK=mainnet python shared/config.py

Dry run:
    python shared/config.py --dry-run
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from ai_economy_sdk import (
    MAINNET,
    TESTNET,
    endpoints_for,
    is_public,
    resolve_network,
    usdc_asset_id,
)
from algosdk.v2client import algod, indexer

NetworkName = Literal["localnet", "testnet", "mainnet"]


@dataclass(frozen=True)
class NetworkConfig:
    """Resolved runtime configuration for Algorand payments."""

    network_name: NetworkName
    network_id: str
    algod_url: str
    algod_token: str
    indexer_url: str
    indexer_token: str
    asset_id: int
    asset_name: str
    asset_decimals: int
    is_public: bool
    fee_payer_funded: bool

    def get_algod_client(self) -> algod.AlgodClient:
        """Construct AlgodClient with configured endpoint and headers."""
        return algod.AlgodClient(self.algod_token, self.algod_url)

    def get_indexer_client(self) -> indexer.IndexerClient:
        """Construct IndexerClient with configured endpoint and headers."""
        return indexer.IndexerClient(self.indexer_token, self.indexer_url)


def load_network_config(network_name: str | None = None) -> NetworkConfig:
    """Load and validate configuration for the requested or environment network.

    Args:
        network_name: Target network ('localnet', 'testnet', 'mainnet').
                     Defaults to the NETWORK environment variable, or 'localnet'.

    Returns:
        Immutable NetworkConfig dataclass.
    """
    raw_name = (network_name or os.environ.get("NETWORK", "localnet")).strip().lower()

    if raw_name in ("localnet", "sandbox", "devnet"):
        name: NetworkName = "localnet"
        algod_url = os.environ.get("ALGOD_URL", "http://localhost:4001")
        algod_token = os.environ.get("ALGOD_TOKEN", "a" * 64)
        indexer_url = os.environ.get("INDEXER_URL", "http://localhost:8980")
        indexer_token = os.environ.get("INDEXER_TOKEN", "a" * 64)

        # Retrieve genesis hash from local algod if available
        try:
            client = algod.AlgodClient(algod_token, algod_url)
            network_id = resolve_network("localnet", client)
        except Exception:
            network_id = "algorand:localnet"

        return NetworkConfig(
            network_name=name,
            network_id=network_id,
            algod_url=algod_url,
            algod_token=algod_token,
            indexer_url=indexer_url,
            indexer_token=indexer_token,
            asset_id=0,  # ALGO native microAlgos
            asset_name="ALGO",
            asset_decimals=6,
            is_public=False,
            fee_payer_funded=True,
        )

    if raw_name in ("testnet", "test"):
        name = "testnet"
        endpoints = endpoints_for(TESTNET)
        algod_url = os.environ.get("ALGOD_URL", endpoints.algod_url)
        algod_token = os.environ.get("ALGOD_TOKEN", endpoints.algod_token)
        indexer_url = os.environ.get("INDEXER_URL", endpoints.indexer_url)
        indexer_token = os.environ.get("INDEXER_TOKEN", endpoints.indexer_token)
        usdc_id = usdc_asset_id(TESTNET) or 10458941

        return NetworkConfig(
            network_name=name,
            network_id=TESTNET,
            algod_url=algod_url,
            algod_token=algod_token,
            indexer_url=indexer_url,
            indexer_token=indexer_token,
            asset_id=usdc_id,
            asset_name="USDC",
            asset_decimals=6,
            is_public=True,
            fee_payer_funded=False,  # Operator must fund fee-payer account with ALGO
        )

    if raw_name in ("mainnet", "prod", "production"):
        name = "mainnet"
        endpoints = endpoints_for(MAINNET)
        algod_url = os.environ.get("ALGOD_URL", endpoints.algod_url)
        algod_token = os.environ.get("ALGOD_TOKEN", endpoints.algod_token)
        indexer_url = os.environ.get("INDEXER_URL", endpoints.indexer_url)
        indexer_token = os.environ.get("INDEXER_TOKEN", endpoints.indexer_token)
        usdc_id = usdc_asset_id(MAINNET) or 31566704

        return NetworkConfig(
            network_name=name,
            network_id=MAINNET,
            algod_url=algod_url,
            algod_token=algod_token,
            indexer_url=indexer_url,
            indexer_token=indexer_token,
            asset_id=usdc_id,
            asset_name="USDC",
            asset_decimals=6,
            is_public=True,
            fee_payer_funded=False,  # Operator must fund fee-payer account with ALGO
        )

    raise ValueError(
        f"Unsupported NETWORK value '{raw_name}'. Expected 'localnet', 'testnet', or 'mainnet'."
    )


# Default singleton instance resolved from current environment
current_config = load_network_config()


def dry_run() -> None:
    """Print resolved configuration for all three supported networks.

    Performs read-only inspection. No transactions or network writes are executed.
    """
    targets: list[NetworkName] = ["localnet", "testnet", "mainnet"]
    print("=" * 72)
    print(" Algorand Payment Network Configuration Matrix (Dry Run)")
    print("=" * 72)

    for target in targets:
        cfg = load_network_config(target)
        print(f"\n[Network: {cfg.network_name.upper()}]")
        print(f"  CAIP-2 Network ID : {cfg.network_id}")
        print(f"  Algod Endpoint    : {cfg.algod_url}")
        print(f"  Indexer Endpoint  : {cfg.indexer_url}")
        print(f"  Payment Asset     : {cfg.asset_name} (Asset ID: {cfg.asset_id})")
        print(f"  Asset Decimals    : {cfg.asset_decimals}")
        print(f"  Public Network    : {cfg.is_public}")
        print(f"  Fee Payer Model   : {'Auto-dispensed (dev)' if not cfg.is_public else 'ALGO funded wallet required'}")

    print("\n" + "=" * 72)
    print(" Dry run completed successfully. 0 transactions submitted.")
    print("=" * 72)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] in ("--dry-run", "dry-run", "all"):
        dry_run()
    else:
        # Default behavior: run dry-run to prove all three network configs
        dry_run()
