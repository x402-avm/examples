/**
 * Browser paywall client application using x402-avm-js.
 *
 * Demonstrates the 402 payment flow in the browser:
 * 1. Requests /api/premium -> catches HTTP 402 with PAYMENT-REQUIRED header.
 * 2. Decodes requirement with decodePaymentRequired().
 * 3. Builds and signs exact AVM payment group with payForRequirement().
 * 4. Retries request with PAYMENT-SIGNATURE header to unlock content.
 */
import { decodePaymentRequired, payForRequirement } from 'x402-avm-js';
import algosdk from 'algosdk';

export async function fetchPremiumContent(
  payerAddress,
  signTxns,
  algodUrl = 'http://localhost:4001',
  algodToken = 'a'.repeat(64)
) {
  // 1. Initial request without payment header
  const initialRes = await fetch('/api/premium');
  if (initialRes.status === 200) {
    return await initialRes.json();
  }
  if (initialRes.status !== 402) {
    throw new Error(`Unexpected server response: HTTP ${initialRes.status}`);
  }

  // 2. Extract PAYMENT-REQUIRED header
  const reqHeader = initialRes.headers.get('payment-required');
  if (!reqHeader) {
    throw new Error('Missing payment-required header in 402 response');
  }

  // 3. Decode payment requirement
  const paymentRequired = decodePaymentRequired(reqHeader);
  const algodClient = new algosdk.Algodv2(algodToken, algodUrl, '');

  // 4. Construct and sign payment group using provided wallet signer callback
  const paymentSignature = await payForRequirement(
    paymentRequired,
    payerAddress,
    algodClient,
    signTxns
  );

  // 5. Retry request with PAYMENT-SIGNATURE header
  const paidRes = await fetch('/api/premium', {
    headers: {
      'payment-signature': paymentSignature,
    },
  });

  if (paidRes.status !== 200) {
    throw new Error(`Payment settlement refused by server: HTTP ${paidRes.status}`);
  }

  return await paidRes.json();
}
