/**
 * Build an X-Identity-Txn proof in JavaScript and verify it with the Python SDK.
 *
 *   node localnet/identity.mjs        # set PYTHON to a interpreter that has ai-economy-sdk
 *
 * The proof is an unsubmitted, zero-fee self-payment signed by the wallet and bound to one
 * network's genesis hash.
 */
import { execFileSync } from 'node:child_process';
import algosdk from 'algosdk';
import { MAINNET, buildIdentityTxn, encodeIdentityHeader } from 'x402-avm-js';

const PYTHON = process.env.PYTHON || 'python3';
const VERIFY = `
import sys
from ai_economy_sdk import verify_identity_txn
print(verify_identity_txn(sys.argv[1], sys.argv[2]))
`;

const account = algosdk.generateAccount();
const address = account.addr.toString();
const txn = buildIdentityTxn(address, MAINNET.genesisHash);
const header = encodeIdentityHeader(txn.signTxn(account.sk));
console.log(`Account:  ${address}`);
console.log(`Header:   ${header.slice(0, 40)}... (${header.length} chars)`);

const verified = execFileSync(PYTHON, ['-c', VERIFY, header, MAINNET.genesisHash], { encoding: 'utf-8' }).trim();
console.log(`Verified: ${verified}`);
if (verified !== address) throw new Error(`Address mismatch: expected ${address}, got ${verified}`);
console.log('Identity proof verified.');
