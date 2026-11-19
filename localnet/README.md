# LocalNet Examples

This directory contains runnable examples and end-to-end integration tests for `x402` payments on Algorand LocalNet (sandbox).

## Contents

- **`_localnet.py`** / **`_localnet.mjs`**: LocalNet helpers (Python and JavaScript) that fund ephemeral test accounts from the KMD dispenser. Every example uses them.
- **`manual_flow.py`**: Manual x402 payment flow without web frameworks on Algorand LocalNet demonstrating direct AVM payment scheme construction, verification, and settlement.
- **`identity.py`**: Cryptographic identity proof verification via zero-fee self-signed Algorand transactions (`X-Identity-Txn` header bound to network genesis hash).
- **`identity.mjs`**: Off-chain wallet identity proof generation with `x402-avm-js` (`buildIdentityTxn`, `encodeIdentityHeader`) and verification via Python `ai_economy_sdk`.
- **`pricing.py`**: Pricing strategies in `ai-economy-sdk` covering fixed per-tool pricing, dynamic price calculation based on arguments, and volume-based bulk discounts.
- **`passes.py`**: Vendor-scoped subscription passes in `ai-economy-sdk` granting zero-charge tool execution verified via on-chain receipt notes.
- **`failed_call_not_charged.py`**: Settle-on-success guarantee proving that tool calls failing with exceptions are never settled on-chain and result in zero balance deduction.
- **`networks.py`**: Network resolution, public endpoints, genesis hashes, and Circle USDC asset identifier inspector for MainNet, TestNet, and LocalNet.
- **`quickstart_server.py`**: FastMCP server payment-gated with `ai-economy-sdk` on port 9201 offering an `echo` tool priced at 5,000 microALGO.
- **`quickstart_client.py`**: Paid MCP client session connecting to `quickstart_server.py` over Streamable HTTP (`/mcp`) on port 9201.
- **`fastapi_paywall.py`**: FastAPI HTTP service protecting `GET /weather` on port 9211 with x402 payment middleware and fee sponsorship (10,000 microALGO), using the shipped `ServerAvmSigner` (about 40 lines).
- **`flask_paywall.py`**: Flask HTTP service protecting `GET /weather` on port 9212 using official x402 Flask middleware with fee sponsorship (10,000 microALGO).
- **`httpx_client.py`**: Automated HTTPX client (`PayerAvmSigner`) that handles 402 challenges, builds zero-fee payments, retries with payment signatures, and verifies settlement against FastAPI (9211) or Flask (9212).
- **`server_for_js.py`**: Minimal FastAPI x402 paywall server on port 9221 designed for JavaScript client payment tests (5,000 microALGO).
- **`js_pay.mjs`**: Full JavaScript x402 client using `x402-avm-js` connecting to `server_for_js.py`, handling 402 negotiation with explicit spend controls (`maxAmount`, `allowedAssets`, ...) and typed `x402-avm-js` errors.
- **`browser_wallet.ts`**: React browser wallet integration wrapper demonstrating signTransactions normalization across Defly, Pera, and Kibisis wallets.
- **`paid_mcp_tool/`**: Tutorial package containing `server.py` (FastMCP server with dynamic length pricing, Streamable HTTP at `http://127.0.0.1:9231/mcp`) and `client.py` (paid MCP client).
- **`browser_paywall/`**: Complete browser application tutorial containing `server.py` (FastAPI backend on port 9232), `app.js` (frontend logic), `index.html`, and `verify.mjs` (Node.js test harness).

---

## Prerequisites

1. AlgoKit LocalNet must be running:
   ```bash
   algokit localnet start
   ```
   Verify health at `http://localhost:4001/health`.

2. Python virtual environment with dependencies installed:
   ```bash
   source .venv/bin/activate
   pip install -r requirements.txt
   npm install
   ```

---

## How to Run Each Example and Expected Output

### 1. Manual AVM Payment Flow (`manual_flow.py`)
Direct construction of payment transactions and verification without an HTTP server.

**Run**:
```bash
python localnet/manual_flow.py
```

**Real Output**:
```text
server 6GX2JKJQHK3DEJAND4ZW7FUPETNE25INUTY6YMANOO2SU4QULTQEEFYZDA
client UEKCYEQCNIXDYNYOT33NPX5VF4ON4LEWDDJWRXUJF5ZGYLBGQLJ3EET4GY
network algorand:tg0cyjEz14FZK9BTpL2q0TOyFbc0McwY
verified payment from UEKCYEQCNIXDYNYOT33NPX5VF4ON4LEWDDJWRXUJF5ZGYLBGQLJ3EET4GY
settled UAPAAALP33WKXKRHF5SMHXRWSJK5UCDGYFH2FVRDENJX5A4LLPMQ in round 1625
```

---

### 2. Python Identity Proofs (`identity.py`)
Generates zero-fee identity transaction proofs and verifies genesis hash bindings.

**Run**:
```bash
python localnet/identity.py
```

**Real Output**:
```text
Address: PMYUCZLJFQ2V4XMA3AXQ54PN2L7NYM2AQKC3BACR6DN7OS37AMWXZSZ7UU
Verified address matches: True
Wrong genesis hash rejected: True
```

---

### 3. JavaScript Identity Proofs (`identity.mjs`)
Generates identity transactions in JavaScript with `x402-avm-js` and verifies against Python `ai_economy_sdk`.

**Run**:
```bash
node localnet/identity.mjs
```

**Real Output**:
```text
Generating test account...
Account address: CVJC3JNVI6UELBEU6BCKZUCISKPNSISUOUU4XHTFTNIE7QYIL6ABYMVL5U
Network genesis hash: wGHE2Pwdvd7S12BL5FaOP20EGYesN73ktiC1qzkkit8=
Identity txn note: x402-identity:CVJC3JNVI6UELBEU6BCKZUCISKPNSISUOUU4XHTFTNIE7QYIL6ABYMVL5U:1795070697
Encoded X-Identity-Txn header: gqNzaWfEQNZUeAlDXUn2PCRCk1ASK4cYy3CmNfT2... (length: 400)

Verifying identity header with Python ai_economy_sdk.verify_identity_txn...
Python verification result: CVJC3JNVI6UELBEU6BCKZUCISKPNSISUOUU4XHTFTNIE7QYIL6ABYMVL5U

Identity proof verified successfully.
```

---

### 4. Pricing Strategies (`pricing.py`)
Demonstrates fixed pricing, argument-based dynamic pricing, and automatic bulk discounts.

**Run**:
```bash
python localnet/pricing.py
```

**Real Output**:
```text
Call 1 (compute - fixed dict price): charge = 6000 microALGO, result = 42
Call 2 (echo - dynamic price 5 words): charge = 5500 microALGO, result = echo: one two three four five
Call 3 (compute - bulk discount 50%): charge = 3000 microALGO, result = 84
```

---

### 5. Vendor-Scoped Passes (`passes.py`)
Demonstrates buying a pass via an on-chain receipt note (`x402-pass:<scope>`) to gain zero-charge access.

**Run**:
```bash
python localnet/passes.py
```

**Real Output**:
```text
Call 1 (without pass): charge = 5000 microALGO, result = echo: without pass
Bought pass on-chain (txid: Q6Z7RQDG...)
Call 2 (with pass): charge = 0 microALGO, result = echo: with pass
```

---

### 6. Settle-on-Success Guarantee (`failed_call_not_charged.py`)
Proves that failed MCP tool executions intercept the payment and avoid settling on-chain.

**Run**:
```bash
python localnet/failed_call_not_charged.py
```

**Real Output**:
```text
Tool call returned (isError=True): Error calling tool 'fail_tool': Deliberate tool failure: computation error
Balance drop: 0 microALGO
```

---

### 7. Networks Inspector (`networks.py`)
Inspects CAIP-2 IDs, genesis hashes, default endpoints, and USDC asset IDs across Algorand networks.

**Run**:
```bash
python localnet/networks.py
```

**Real Output**:
```text
Network    | CAIP-2 Identifier                            | Genesis Hash                                   | USDC ID    | Algod Endpoint                      | Indexer Endpoint                   
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
mainnet    | algorand:wGHE2Pwdvd7S12BL5FaOP20EGYesN73k    | wGHE2Pwdvd7S12BL5FaOP20EGYesN73ktiC1qzkkit8=   | 31566704   | https://mainnet-api.algonode.cloud  | https://mainnet-idx.algonode.cloud 
testnet    | algorand:SGO1GKSzyE7IEPItTxCByw9x8FmnrCDe    | SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=   | 10458941   | https://testnet-api.algonode.cloud  | https://testnet-idx.algonode.cloud 
localnet   | algorand:tg0cyjEz14FZK9BTpL2q0TOyFbc0McwY    | tg0cyjEz14FZK9BTpL2q0TOyFbc0McwYsFJbszmFANk=   | None       | http://localhost:4001               | http://localhost:8980              
```

---

### 8. TypeScript Browser Wallet Type-Checking (`browser_wallet.ts`)
Validates that browser wallet integration types match `@txnlab/use-wallet-react` and `x402-avm-js`.

**Run**:
```bash
npm run typecheck
```

**Real Output**:
```text
> x402-avm-examples@0.1.0 typecheck
> tsc --noEmit localnet/browser_wallet.ts --skipLibCheck
```
*(Process exits 0 with no errors)*

---

### 9. Quickstart Server & Client (Port 9201)
FastMCP server monetized with `PaymentGate` and client session via `paid_mcp_session`.

**Run**:
```bash
# Terminal 1: Start server
python localnet/quickstart_server.py

# Terminal 2: Run client
python localnet/quickstart_client.py
```

**Real Output**:
```text
pay_to: ZHYKRANDKD32WWIEK5QXSI357WA3CEX3F6YANLUJDM52XJOTCP2MCENPM4
Result: echo: hello world
Balance drop: 5000 microALGO
```

---

### 10. FastAPI Paywall Server & HTTPX Client (Port 9211)
FastAPI service protecting `GET /weather` with x402 payment middleware.

**Run**:
```bash
# Terminal 1: Start server
python localnet/fastapi_paywall.py

# Terminal 2: Run client
python localnet/httpx_client.py --url http://127.0.0.1:9211/weather
```

**Real Output**:
```text
200 {'city': 'Boston', 'temperature': 68, 'network': 'algorand:tg0cyjEz14FZK9BTpL2q0TOyFbc0McwY'}
Paid exactly 10000 microALGO.
```

---

### 11. Flask Paywall Server & HTTPX Client (Port 9212)
Flask service protecting `GET /weather` with x402 payment middleware.

**Run**:
```bash
# Terminal 1: Start server
python localnet/flask_paywall.py

# Terminal 2: Run client
python localnet/httpx_client.py --url http://127.0.0.1:9212/weather
```

**Real Output**:
```text
200 {'city': 'Boston', 'temperature': 68, 'network': 'algorand:tg0cyjEz14FZK9BTpL2q0TOyFbc0McwY'}
Paid exactly 10000 microALGO.
```

---

### 12. Server for JavaScript & JS Pay Client (Port 9221)
Node.js client using `x402-avm-js` paying against a FastAPI service.

**Run**:
```bash
# Terminal 1: Start server
python localnet/server_for_js.py

# Terminal 2: Run client
node localnet/js_pay.mjs
```

**Real Output**:
```text
Server asks 5000 units of asset 0 -> YOBKKEON3OT6MO756ERG4IUGCSFTYBYJMMYTKTGQWE5CFDTR37ZX5VF3Z4
Paid response: 200 {
  status: 'ok',
  data: 'Access granted to premium resource',
  txid: 'ENPZ5LHJQF6KOVVYAKSNPVSWXKI63KMIFUYFC4ZCNWJUF3FKOIJA',
  payer: 'HRFE3P7VETPT2WOIHQX5CHWVULSX7OSLDTSNQ3JR5KTBBJKO5YTJWTG34Q'
}
Balance drop: 5000 microALGO
Over-cap request rejected: SpendLimitExceededError
```

---

### 13. Paid MCP Tool Server & Client (Port 9231)
Dynamic length pricing for MCP summarize tool.

**Run**:
```bash
# Terminal 1: Start server
python localnet/paid_mcp_tool/server.py

# Terminal 2: Run client
python localnet/paid_mcp_tool/client.py
```

**Real Output**:
```text
Server starting on http://127.0.0.1:9231/mcp ...
Generating funded buyer account on LocalNet...
Opening paid MCP session to http://127.0.0.1:9231/mcp ...
Calling summarize tool...
Result: Algorand is a pure proof-of-stake blockchain. It achieves immediate finality without forks.
Price paid: 3000 microALGO
Confirmed TxID: 6KZ7HVYKA27AAFTQLKOG7NSJ3FZ3VMS2A25DYVYEMRAQ2XTQSUGQ (confirmed at round 1651)
```

---

### 14. Browser Paywall Tutorial & Verification (Port 9232)
Full web paywall bundling and Node.js verification client.

**Run**:
```bash
# Build frontend bundle
npm run build:paywall

# Terminal 1: Start server
python localnet/browser_paywall/server.py

# Terminal 2: Run verification client
node localnet/browser_paywall/verify.mjs
```

**Real Output**:
```text
Browser paywall on http://127.0.0.1:9232
402: 4000 units of asset 0 to E6LKFN454US4LLBF2DJ4OFVZ7VVWCV2PMWTNIR4QVOQGGDEMKUEXLUFMNA on algorand:tg0cyjEz14FZK9BTpL2q0TOyFbc0McwY
Unlocked: {
  title: 'Deep Sea Hydrothermal Vent Survey',
  findings: 'Dense polymetallic sulfides discovered at depth 2,400m.',
  status: 'unlocked'
}
Balance drop: 4000 microALGO
Browser paywall verified.
```

---

### 15. Automated Test Suite Runner
Runs all 13 LocalNet integration tests sequentially with automatic background server lifecycle management and port verification:

**Run**:
```bash
bash scripts/run_all_localnet.sh
```

**Output**:
```text
======================================================================
 ALL 13 LOCALNET EXAMPLES PASSED SUCCESSFULLY!
======================================================================
```
