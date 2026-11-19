/**
 * Pay an x402 paywall from JavaScript on LocalNet (start server_for_js.py first, port 9221).
 *
 *   node localnet/js_pay.mjs
 *
 * Fetch -> 402 -> decodePaymentRequired -> payForRequirement (with explicit spend controls)
 * -> retry with PAYMENT-SIGNATURE -> check the exact 5000 microALGO balance drop.
 */
import { SpendLimitExceededError, X402AvmError, decodePaymentRequired, payForRequirement } from 'x402-avm-js';
import { algod, newFundedAccount, signerFor } from './_localnet.mjs';

const URL = 'http://127.0.0.1:9221/paid';
const balance = async (addr) => (await algod.accountInformation(addr).do()).amount;

const buyer = await newFundedAccount();
const before = await balance(buyer.address);

const res402 = await fetch(URL);
if (res402.status !== 402) throw new Error(`Expected 402, got ${res402.status}`);
const challenge = decodePaymentRequired(res402.headers.get('payment-required'));
const [req] = challenge.accepts;
console.log(`Server asks ${req.amount} units of asset ${req.asset} -> ${req.payTo}`);

// Spend controls are checked before anything is signed. The default cap is 1,000,000 base units;
// here we tighten it and pin the asset, network and recipient.
const controls = {
  maxAmount: 10_000n,
  allowedAssets: ['0'],
  allowedNetworks: [req.network],
  allowedPayTo: [req.payTo],
};

try {
  const signature = await payForRequirement(challenge, buyer.address, algod, signerFor(buyer.sk), controls);
  const paid = await fetch(URL, { headers: { 'payment-signature': signature } });
  console.log(`Paid response: ${paid.status}`, await paid.json());
} catch (err) {
  if (err instanceof SpendLimitExceededError) throw new Error(`Refused to overpay: ${err.message}`);
  if (err instanceof X402AvmError) throw new Error(`x402 error ${err.code}: ${err.message}`);
  throw err;
}

const drop = before - (await balance(buyer.address));
console.log(`Balance drop: ${drop} microALGO`);
if (drop !== 5000n) throw new Error(`Expected a drop of 5000 microALGO, got ${drop}`);

// A 50,000 microALGO demand would exceed the 10,000 cap and is refused without signing.
const greedy = { ...challenge, accepts: [{ ...req, amount: '50000' }] };
await payForRequirement(greedy, buyer.address, algod, signerFor(buyer.sk), controls).then(
  () => { throw new Error('Spend cap did not trigger'); },
  (err) => console.log(`Over-cap request rejected: ${err.constructor.name}`),
);
