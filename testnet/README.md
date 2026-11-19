# TestNet Examples

This directory contains examples for validating and executing `x402` Algorand payments on Algorand TestNet (`algorand:SGO1GKSzyE7IEPItTxCByw9x8FmnrCDe`).

## Contents

- **`simulate.py`**: Read-only simulation for x402 Algorand payments on TestNet evaluating ALGO and USDC payment groups against live ledger state using empty signatures without spending funds.
- **`simulate.mjs`**: Read-only simulation of ALGO and USDC payments on Algorand TestNet in JavaScript using `x402-avm-js` and `algosdk` with a watch-only signer.
- **`live_payment.py`**: Optional live TestNet payment execution template for x402 on Algorand that settles real on-chain transactions when explicit environment variables are configured.

---

## Keys & Security

> [!WARNING]
> Never use or configure MainNet private keys, mnemonics, or credentials for TestNet examples. Never commit `.env` or any secret files to version control.

The `live_payment.py` script reads 25-word Algorand account mnemonics from the environment:
- `TESTNET_BUYER_MNEMONIC`: 25-word mnemonic for the client / buyer account.
- `TESTNET_SERVER_MNEMONIC`: 25-word mnemonic for the resource server / fee payer account.

### How to Fund a Throwaway TestNet Account
1. Generate fresh throwaway accounts for testing (e.g. via AlgoKit or `algosdk.account.generate_account()`).
2. Dispense free TestNet ALGO from the official TestNet dispenser:
   - **TestNet Dispenser**: [https://bank.testnet.algorand.network/](https://bank.testnet.algorand.network/)
3. Keep credentials strictly in local environment variables:
   ```bash
   export TESTNET_BUYER_MNEMONIC="word1 word2 ... word25"
   export TESTNET_SERVER_MNEMONIC="word1 word2 ... word25"
   ```
4. If either environment variable is omitted or empty, `live_payment.py` automatically skips on-chain execution and exits cleanly with status code `0`.

---

## How to Run Each Example and Expected Output

### 1. Python TestNet Read-Only Simulation (`simulate.py`)
Queries the public AlgoNode indexer for real funded TestNet accounts holding ALGO and TestNet USDC (ASA ID `10458941`), constructs atomic payment groups (with and without fee payer sponsorship), and evaluates them against Algod's `/v2/transactions/simulate` endpoint with empty signatures.

**Run**:
```bash
python testnet/simulate.py
```

**Real Output**:
```text
Testing testnet (algorand:SGO1GKSzyE7IEPItTxCByw9x8FmnrCDe)...
  testnet ALGO (fee_payer=True): ok
  testnet ALGO (fee_payer=False): ok
  testnet USDC (fee_payer=True): ok
  testnet USDC (fee_payer=False): ok
All testnet simulations passed successfully.
```

---

### 2. JavaScript TestNet Read-Only Simulation (`simulate.mjs`)
Demonstrates the equivalent watch-only simulation flow in Node.js using `x402-avm-js` and `algosdk`.

**Run**:
```bash
node testnet/simulate.mjs
```

**Real Output**:
```text
Testing testnet (algorand:SGO1GKSzyE7IEPItTxCByw9x8FmnrCDe)...
Discovered active accounts:
  Payer:     AAEYHQNBDIXJQHWSOUMPMAPAYVLXYRZ74R3BR6T5IYRTCLSJIEDJUII3FM
  PayTo:     AAJSPJJEMGQILKIIWRLOGHBEUDZLKWBZWGFOFH4EIZNTEZ5EBKLBYAD7NQ
  Fee payer: AAJWOVGEF26RFOUMVGDIF665CVVL645JYDC26V2UB4MQR5JPZNR27GAZJE
  testnet ALGO (fee_payer=true): ok
  testnet ALGO (fee_payer=false): ok
  testnet USDC (fee_payer=true): ok
  testnet USDC (fee_payer=false): ok
All testnet simulations passed successfully.
```

---

### 3. Live TestNet Payment Execution (`live_payment.py`)
Executes an actual on-chain transaction only when credentials are provided in the environment.

**Run**:
```bash
python testnet/live_payment.py
```

**Output without Environment Variables (Default)**:
```text
TestNet live payment example requires environment variables:
  TESTNET_BUYER_MNEMONIC: 25-word mnemonic for buyer account on TestNet
  TESTNET_SERVER_MNEMONIC: 25-word mnemonic for server account on TestNet

TestNet ALGO can be obtained for free from https://lora.algokit.io/testnet/fund.
Environment variables not set; skipping live on-chain payment.
```
