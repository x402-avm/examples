# Shared Utilities

This directory contains cross-cutting utilities and configuration modules shared across LocalNet, TestNet, and MainNet examples.

## Contents

- **`config.py`**: Multi-network runtime configuration manager that resolves Algorand endpoints, network IDs, and payment asset configurations based on the `NETWORK` environment variable (`localnet`, `testnet`, or `mainnet`).

## Usage

```bash
# Dry run inspection of all networks
python shared/config.py --dry-run

# Targeted network inspection
NETWORK=localnet python shared/config.py
NETWORK=testnet python shared/config.py
NETWORK=mainnet python shared/config.py
```
