# MainNet Examples

This directory contains public network simulation examples for `x402` Algorand payments on Algorand MainNet (`algorand:wGHE2Pwdvd7S12BL5FaOP20EGYesN73k`).

> [!IMPORTANT]
> **Simulate-Only (Zero Spend)**:
> All examples in this folder are **strictly read-only simulations**. They construct and evaluate atomic transaction groups against live MainNet node state using Algod's `/v2/transactions/simulate` endpoint with empty signatures. **No funds are spent, and no transactions are broadcast to the network.**

For production deployment instructions, real USDC settlement, fee payer funding, and security considerations, see the official documentation:
- **MainNet Production Guide**: [https://x402-avm.github.io/guides/networks/mainnet](https://x402-avm.github.io/guides/networks/mainnet)

---

## Contents

- **`simulate.py`**: Read-only simulation for x402 Algorand payments on MainNet evaluating ALGO (asset 0) and Circle USDC (asset 31566704) payment groups against real ledger accounts using empty signatures without spending funds.
- **`simulate.mjs`**: Read-only simulation of ALGO and USDC payments on Algorand MainNet in JavaScript using `x402-avm-js` and `algosdk` with a watch-only signer and explicit spend controls (`maxAmount`, typed `X402AvmError`).

*(Note: Multi-network runtime configuration has moved to [`shared/config.py`](../shared/config.py)).*

---

## How to Run Each Example and Expected Output

### 1. Python MainNet Read-Only Simulation (`simulate.py`)
Queries the public AlgoNode indexer for real funded MainNet accounts holding ALGO and MainNet USDC (ASA ID `31566704`), builds atomic payment groups (with and without fee payer sponsorship), and evaluates them against Algod's `/v2/transactions/simulate` endpoint.

**Run**:
```bash
python mainnet/simulate.py
```

**Real Output**:
```text
Testing mainnet (algorand:wGHE2Pwdvd7S12BL5FaOP20EGYesN73k)...
  mainnet ALGO (fee_payer=True): ok
  mainnet ALGO (fee_payer=False): ok
  mainnet USDC (fee_payer=True): ok
  mainnet USDC (fee_payer=False): ok
All mainnet simulations passed successfully.
```

---

### 2. JavaScript MainNet Read-Only Simulation (`simulate.mjs`)
Demonstrates the equivalent watch-only simulation flow in Node.js using `x402-avm-js` and `algosdk`.

**Run**:
```bash
node mainnet/simulate.mjs
```

**Real Output**:
```text
Testing mainnet (algorand:wGHE2Pwdvd7S12BL5FaOP20EGYesN73k)...
Discovered active accounts:
  Payer:     AAC2JBF6S6WIFE3SIWKDJ46HOBOXFBGBMMMSJDMIBE25SMBG4H2D2TJ3XY
  PayTo:     AAKAX2W6CYA6P53EW33ZAP4KGCNPONZRTGX4HHGABQXSWDW4MJY7Z4K4HM
  Fee payer: AAKDUROSZLMO6WYSWIBTVQNYWIMGYSBYS7TT5ESBZUWZBFLACP3RLZHBUQ
  mainnet ALGO (fee_payer=true): ok
  mainnet ALGO (fee_payer=false): ok
  mainnet USDC (fee_payer=true): ok
  mainnet USDC (fee_payer=false): ok
All mainnet simulations passed successfully.
```
