/**
 * Runs the same x402 client flow as app.js from Node against the paywall on port 9232
 * (start browser_paywall/server.py first):
 *
 *   node localnet/browser_paywall/verify.mjs
 */
import { decodePaymentRequired, payForRequirement } from 'x402-avm-js';
import { algod, newFundedAccount, signerFor } from '../_localnet.mjs';

const URL = 'http://127.0.0.1:9232/api/premium';
const balance = async (addr) => (await algod.accountInformation(addr).do()).amount;

const buyer = await newFundedAccount(5);
const before = await balance(buyer.address);

const res402 = await fetch(URL);
if (res402.status !== 402) throw new Error(`Expected 402, got ${res402.status}`);
const challenge = decodePaymentRequired(res402.headers.get('payment-required'));
const [req] = challenge.accepts;
console.log(`402: ${req.amount} units of asset ${req.asset} to ${req.payTo} on ${req.network}`);

const signature = await payForRequirement(challenge, buyer.address, algod, signerFor(buyer.sk));
const paid = await fetch(URL, { headers: { 'payment-signature': signature } });
if (paid.status !== 200) throw new Error(`Expected 200, got ${paid.status}: ${await paid.text()}`);
console.log('Unlocked:', await paid.json());

const drop = before - (await balance(buyer.address));
console.log(`Balance drop: ${drop} microALGO`);
if (drop !== BigInt(req.amount)) throw new Error(`Expected a drop of ${req.amount}, got ${drop}`);
console.log('Browser paywall verified.');
