/**
 * Off-chain wallet identity proof generation and verification.
 *
 * Demonstrates:
 * 1. Constructing an unsubmitted, zero-fee identity transaction using buildIdentityTxn().
 * 2. Signing the identity transaction with the wallet private key.
 * 3. Encoding the signed transaction into the X-Identity-Txn header value via encodeIdentityHeader().
 * 4. Verifying the cryptographic proof using Python ai_economy_sdk.verify_identity_txn via subprocess.
 *
 * How to run:
 *   node localnet/identity.mjs
 *
 * What it prints:
 *   Generated address, encoded identity header, and the verified address returned by Python.
 */

import { execFileSync } from 'child_process';
import algosdk from 'algosdk';
import {
  MAINNET,
  buildIdentityTxn,
  encodeIdentityHeader,
} from 'x402-avm-js';

const PYTHON_BIN = process.env.PYTHON || 'python3';

async function main() {
  console.log('Generating test account...');
  const account = algosdk.generateAccount();
  const address = account.addr.toString();
  console.log(`Account address: ${address}`);

  const genesisHash = MAINNET.genesisHash;
  console.log(`Network genesis hash: ${genesisHash}`);

  // 1. Build unsubmitted 0-fee self-payment transaction
  const txn = buildIdentityTxn(address, genesisHash);
  console.log(`Identity txn note: ${new TextDecoder().decode(txn.note)}`);

  // 2. Sign transaction with account secret key
  const signedBytes = txn.signTxn(account.sk);

  // 3. Encode to base64 header value
  const headerValue = encodeIdentityHeader(signedBytes);
  console.log(`Encoded X-Identity-Txn header: ${headerValue.slice(0, 40)}... (length: ${headerValue.length})`);

  // 4. Verify identity transaction with Python ai_economy_sdk.verify_identity_txn
  console.log('\nVerifying identity header with Python ai_economy_sdk.verify_identity_txn...');
  const pythonScript = `
import sys, json
from ai_economy_sdk import verify_identity_txn
header = sys.argv[1]
gh = sys.argv[2]
verified_addr = verify_identity_txn(header, gh)
print(json.dumps({"verified_address": verified_addr}))
`;

  const stdout = execFileSync(PYTHON_BIN, ['-c', pythonScript, headerValue, genesisHash], {
    encoding: 'utf-8',
  });

  const result = JSON.parse(stdout.trim());
  console.log(`Python verification result: ${result.verified_address}`);

  if (result.verified_address !== address) {
    throw new Error(`Address mismatch: expected ${address}, got ${result.verified_address}`);
  }

  console.log('\nIdentity proof verified successfully.');
}

main().catch((err) => {
  console.error('Identity verification failed:', err);
  process.exit(1);
});
