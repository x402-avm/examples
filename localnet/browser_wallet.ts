/**
 * React browser wallet integration using use-wallet-react v5 and x402-avm-js.
 *
 * Demonstrates:
 * 1. Connecting to active wallet account, algod client, and signTransactions hook.
 * 2. Normalizing the signTransactions return contract across different wallet providers.
 * 3. Calling payForRequirement() to fulfill an x402 payment challenge.
 *
 * How to type-check:
 *   npx tsc --noEmit localnet/browser_wallet.ts
 */

import { useWallet } from '@txnlab/use-wallet-react';
import { payForRequirement, type PaymentRequired, type SpendControls } from 'x402-avm-js';

/**
 * Execute an x402 payment challenge using the connected browser wallet.
 *
 * Different wallet providers implement the signTransactions contract in two ways:
 * - Full-group mapping: Returns an array of length equal to txns.length, with null at un-signed indexes.
 * - Sparse mapping: Returns an array of length equal to indexes.length, containing only requested signatures.
 *
 * The wrapper normalizes both behaviors to match payForRequirement's expectation:
 * an array of length txns.length with Uint8Array at signed indexes and null elsewhere.
 *
 * @param challenge - Decoded PaymentRequired challenge from HTTP 402 response.
 * @param wallet - useWallet() hook return value.
 * @param controls - Spend controls; without them the default cap of 1,000,000 base units applies.
 *   Throws SpendLimitExceededError / PaymentNotAllowedError (both X402AvmError) before the wallet is asked to sign.
 * @returns Promise resolving to the base64-encoded PAYMENT-SIGNATURE header.
 */
export async function payWithBrowserWallet(
  challenge: PaymentRequired,
  wallet: ReturnType<typeof useWallet>,
  controls: SpendControls = { maxAmount: 100_000n, allowedAssets: ['0'] },
): Promise<string> {
  const { activeAddress, algodClient, signTransactions } = wallet;

  if (!activeAddress) {
    throw new Error('No active wallet connected. Please connect your wallet first.');
  }

  // Normalize wallet signing response to full group length
  const safeSignTxns = async (
    txns: Uint8Array[],
    indexes: number[]
  ): Promise<(Uint8Array | null)[]> => {
    const signed = await signTransactions(txns, indexes);
    if (!signed) {
      return new Array(txns.length).fill(null);
    }

    const mapped: (Uint8Array | null)[] = new Array(txns.length).fill(null);
    if (signed.length === indexes.length) {
      indexes.forEach((txnIdx, signIdx) => {
        mapped[txnIdx] = signed[signIdx];
      });
    } else {
      signed.forEach((signedBytes, idx) => {
        if (signedBytes) {
          mapped[idx] = signedBytes;
        }
      });
    }
    return mapped;
  };

  return await payForRequirement(challenge, activeAddress, algodClient, safeSignTxns, controls);
}
