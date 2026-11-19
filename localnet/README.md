# LocalNet Examples

This directory contains runnable examples and end-to-end integration tests for `x402` payments on Algorand LocalNet (sandbox).

## Contents

- **`_localnet.py`**: LocalNet helper module that dispenses funds to ephemeral test accounts using the LocalNet KMD dispenser.
- **`manual_flow.py`**: Manual x402 payment flow without web frameworks on Algorand LocalNet demonstrating direct AVM payment scheme construction, verification, and settlement.
- **`identity.py`**: Cryptographic identity proof verification via zero-fee self-signed Algorand transactions (`X-Identity-Txn` header bound to network genesis hash).
- **`identity.mjs`**: Off-chain wallet identity proof generation with `x402-avm-js` (`buildIdentityTxn`, `encodeIdentityHeader`) and verification via Python `ai_economy_sdk`.
- **`pricing.py`**: Pricing strategies in `ai-economy-sdk` covering fixed per-tool pricing, dynamic price calculation based on arguments, and volume-based bulk discounts.
- **`passes.py`**: Vendor-scoped subscription passes in `ai-economy-sdk` granting zero-charge tool execution verified via on-chain receipt notes.
- **`failed_call_not_charged.py`**: Settle-on-success guarantee proving that tool calls failing with exceptions are never settled on-chain and result in zero balance deduction.
- **`networks.py`**: Network resolution, public endpoints, genesis hashes, and Circle USDC asset identifier inspector for MainNet, TestNet, and LocalNet.
- **`quickstart_server.py`**: FastMCP server payment-gated with `ai-economy-sdk` on port 9201 offering an `echo` tool priced at 5,000 microALGO.
- **`quickstart_client.py`**: Paid MCP client session connecting to `quickstart_server.py` via SSE on port 9201.
- **`fastapi_paywall.py`**: FastAPI HTTP service protecting `GET /weather` on port 9211 with x402 payment middleware and fee sponsorship (10,000 microALGO).
- **`flask_paywall.py`**: Flask HTTP service protecting `GET /weather` on port 9212 using official x402 Flask middleware with fee sponsorship (10,000 microALGO).
- **`httpx_client.py`**: Automated HTTPX client that handles 402 challenges, builds zero-fee payments, retries with payment signatures, and verifies settlement against FastAPI (9211) or Flask (9212).
- **`server_for_js.py`**: Minimal FastAPI x402 paywall server on port 9221 designed for JavaScript client payment tests (5,000 microALGO).
- **`js_pay.mjs`**: Full JavaScript x402 client using `x402-avm-js` connecting to `server_for_js.py`, handling 402 challenge negotiation and verifying exact balance deduction.
- **`browser_wallet.ts`**: React browser wallet integration wrapper demonstrating signTransactions normalization across Defly, Pera, and Kibisis wallets.
- **`paid_mcp_tool/`**: Tutorial package containing `server.py` (FastMCP server with dynamic length pricing on port 9231) and `client.py` (paid MCP client).
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
Server address: G3RH5P4MU4PDLF3EAVTGTWPIOYSJOIG6H75EGDVPP5DI2QH4WDPR7OS6FU
Client address: AFUPSX2HBZPAIOGOJWMGB47XD4L5VL2EIUTP2APDNTAF7K5P3TGS7GS6NI
Network: algorand:tg0cyjEz14FZK9BTpL2q0TOyFbc0McwY
Verification successful: Valid payment from AFUPSX2HBZPAIOGOJWMGB47XD4L5VL2EIUTP2APDNTAF7K5P3TGS7GS6NI
Settled transaction ID: DO3ODTYEQKDZZX444VCVLCUGZR24L435XI4QC6CFZNTEODOMRJLA
Confirmed round: 1367
Manual payment flow completed successfully.
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
pay_to: QBADOZH6JS4E4YHZRZXXG6RJJLG3MTLZ2BM3CGC7HI5G2MCQ77PXOH5IYE
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
Buyer address: GJQ7GKVVKQ3HMBUSADS2CUJAWYFZQFRJHIIUWXARGFA3HUGH4JU5LHURPQ
Buyer initial balance: 5000000 microALGO
Requesting GET http://127.0.0.1:9211/weather...
Response status: 200
Response body: {'city': 'Boston', 'temperature': 68, 'conditions': 'sunny', 'network': 'algorand:tg0cyjEz14FZK9BTpL2q0TOyFbc0McwY'}
Buyer final balance: 4990000 microALGO
Balance drop: 10000 microALGO
Verification SUCCESS: Balance drop equals exactly 10,000 microALGO.
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
Buyer address: ERGEGGMYVZ6NXNMRZM5AGPYM7SPO3AS6T4VELOHAVVRPSTIWNPWYAJ5VVQ
Buyer initial balance: 5000000 microALGO
Requesting GET http://127.0.0.1:9212/weather...
Response status: 200
Response body: {'city': 'Boston', 'conditions': 'sunny', 'network': 'algorand:tg0cyjEz14FZK9BTpL2q0TOyFbc0McwY', 'temperature': 68}
Buyer final balance: 4990000 microALGO
Balance drop: 10000 microALGO
Verification SUCCESS: Balance drop equals exactly 10,000 microALGO.
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
Created buyer account: VIZCOCQ3ONRUTMZV2IWLDK272IWC526PJZKBYTFLZVMSGPSJL4SXDMNMY4
Initial buyer balance: 10000000 microALGO

Fetching http://127.0.0.1:9221/paid without payment...
Initial response status: 402
Decoded x402 challenge version: 2
Accepted requirement: 5000 units of asset 0 to 7NJTDIUBOQZJD3AA4TVJTE6P35XDNF44VEJW2QTOGFT7GILPV4HH2F6EJQ
Payment signature header constructed (length: 1744)

Retrying http://127.0.0.1:9221/paid with PAYMENT-SIGNATURE...
Paid response status: 200
Response payload: {"status":"ok","data":"Access granted to premium resource","txid":"IOKBB5IQSJQZ6CU6YYAH2CES2QKOL3OMGIYJG55DRJ7K5DGT3ETQ","payer":"VIZCOCQ3ONRUTMZV2IWLDK272IWC526PJZKBYTFLZVMSGPSJL4SXDMNMY4"}
Final buyer balance: 9995000 microALGO
Balance drop: 5000 microALGO

Payment completed and verified successfully.
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
Server starting on http://127.0.0.1:9231 ...
Generating funded buyer account on LocalNet...
Opening paid MCP session to http://127.0.0.1:9231/sse ...
Calling summarize tool...
Result: Algorand is a pure proof-of-stake blockchain. It achieves immediate finality without forks.
Price paid: 3000 microALGO
Confirmed TxID: BS5O3NMD2YAD2YQLQSWNFQM25AMDJL5JHQI4RZP5O3ZRAL64LWZA (confirmed at round 1418)
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
Server starting on http://127.0.0.1:9232 ...
--- Browser Paywall Verification (Node.js) ---
Note: The browser page itself is not run; this script tests the exact x402 functions used in app.js.

1. Generating funded buyer account on LocalNet...
Buyer account: DE6HJLB4ED5KLH4HB6SB4E4PPEMT5OX3FRNBUITVDKIIBPN5KRMG3S7HPY
Initial balance: 5000000 microALGO (5 ALGO)

2. Sending initial unauthenticated request to GET /api/premium ...
Received status: HTTP 402
Decoded PAYMENT-REQUIRED header...
- Scheme: exact
- Price: 4000 microALGO (asset: 0)
- Pay To: 3T4ILPVSFK3ZF2T47OC2CBJSF32KUYGFYDN6PHKNOW2RIIOCYOUCTL6ZY4
- Network: algorand:tg0cyjEz14FZK9BTpL2q0TOyFbc0McwY

3. Building and signing exact AVM payment group with x402-avm-js...
Generated PAYMENT-SIGNATURE header.

4. Retrying request with PAYMENT-SIGNATURE header...
Received status: HTTP 200
Unlocked content:
{
  "title": "Deep Sea Hydrothermal Vent Survey",
  "findings": "Dense polymetallic sulfides discovered at depth 2,400m.",
  "status": "unlocked"
}

5. Verifying on-chain balance change...
Final balance: 4996000 microALGO
Balance drop: 4000 microALGO (price: 4000 microALGO)

=== VERIFICATION SUCCESS: HTTP 200 received and balance drop confirmed! ===
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
