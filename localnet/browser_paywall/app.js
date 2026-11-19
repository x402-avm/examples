/**
 * Browser paywall client (x402-avm-js): fetch /api/premium, pay the 402 challenge with the
 * caller's wallet signer, retry with PAYMENT-SIGNATURE.
 */
import algosdk from 'algosdk';
import { PaymentNotAllowedError, SpendLimitExceededError, decodePaymentRequired, payForRequirement } from 'x402-avm-js';

// Never pay more than 0.01 ALGO per request, whatever the server asks for.
const SPEND_CONTROLS = { maxAmount: 10_000n, allowedAssets: ['0'] };

export async function fetchPremiumContent(
  payerAddress,
  signTxns,
  algodUrl = 'http://localhost:4001',
  algodToken = 'a'.repeat(64),
) {
  const first = await fetch('/api/premium');
  if (first.status === 200) return first.json();
  if (first.status !== 402) throw new Error(`Unexpected server response: HTTP ${first.status}`);

  const challenge = decodePaymentRequired(first.headers.get('payment-required'));
  const algod = new algosdk.Algodv2(algodToken, algodUrl, '');

  let signature;
  try {
    signature = await payForRequirement(challenge, payerAddress, algod, signTxns, SPEND_CONTROLS);
  } catch (err) {
    if (err instanceof SpendLimitExceededError || err instanceof PaymentNotAllowedError) {
      throw new Error(`Payment refused by spend controls: ${err.message}`);
    }
    throw err;
  }

  const paid = await fetch('/api/premium', { headers: { 'payment-signature': signature } });
  if (paid.status !== 200) throw new Error(`Payment refused by server: HTTP ${paid.status}`);
  return paid.json();
}
