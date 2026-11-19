/**
 * Read-only simulation of ALGO and USDC payments on Algorand MainNet.
 *
 * Demonstrates:
 * 1. Discovering real funded USDC holders via public AlgoNode indexer endpoints.
 * 2. Building exact AVM payment groups using a watch-only signer (empty signatures).
 * 3. Verifying transaction group validity on live MainNet nodes using algod.simulateTransactions().
 * 4. Verifying both native ALGO and ASA USDC transfers, with and without fee payers.
 *
 * How to run:
 *   node mainnet/simulate.mjs
 *
 * What it prints:
 *   Found account addresses on MainNet and "ok" for each simulated payment scenario.
 */

import algosdk from 'algosdk';
import {
  MAINNET,
  algodClient,
  payForRequirement,
} from 'x402-avm-js';

async function fundedUsdcHolders(net, algod) {
  const url = `${net.indexerUrl}/v2/assets/${net.usdc}/balances?currency-greater-than=5000000&limit=40`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Indexer query failed with status ${res.status}`);
  }
  const rows = (await res.json()).balances;
  const out = [];
  for (const row of rows) {
    const info = await algod.accountInformation(row.address).do();
    if (info.amount - info.minBalance > 2_000_000n && !info.authAddr) {
      out.push(row.address);
    }
    if (out.length === 3) return out;
  }
  throw new Error(`Not enough funded USDC holders found on ${net.genesisId}`);
}

async function main() {
  const name = 'mainnet';
  const net = MAINNET;
  console.log(`Testing ${name} (${net.caip2})...`);
  const algod = algodClient(name);

  const [payer, payTo, feePayer] = await fundedUsdcHolders(net, algod);
  console.log(`Discovered active accounts:`);
  console.log(`  Payer:     ${payer}`);
  console.log(`  PayTo:     ${payTo}`);
  console.log(`  Fee payer: ${feePayer}`);

  const cases = [
    { asset: 'ALGO', assetId: '0', withFeePayer: true },
    { asset: 'ALGO', assetId: '0', withFeePayer: false },
    { asset: 'USDC', assetId: String(net.usdc), withFeePayer: true },
    { asset: 'USDC', assetId: String(net.usdc), withFeePayer: false },
  ];

  for (const c of cases) {
    const requirement = {
      scheme: 'exact',
      network: net.caip2,
      asset: c.assetId,
      amount: '10000',
      payTo,
      maxTimeoutSeconds: 300,
      extra: c.withFeePayer ? { feePayer } : {},
    };

    const emptySigner = async (txns) => txns.map(() => null);

    const challenge = {
      x402Version: 2,
      accepts: [requirement],
    };

    const paymentSignatureHeader = await payForRequirement(challenge, payer, algod, emptySigner);
    const decoded = JSON.parse(new TextDecoder().decode(algosdk.base64ToBytes(paymentSignatureHeader)));

    const txns = decoded.payload.paymentGroup.map(
      (b64) =>
        new algosdk.SignedTransaction({
          txn: algosdk.decodeUnsignedTransaction(algosdk.base64ToBytes(b64)),
        })
    );

    const sim = await algod
      .simulateTransactions(
        new algosdk.modelsv2.SimulateRequest({
          txnGroups: [new algosdk.modelsv2.SimulateRequestTransactionGroup({ txns })],
          allowEmptySignatures: true,
        })
      )
      .do();

    const failure = sim.txnGroups[0].failureMessage ?? null;
    if (failure) {
      throw new Error(`Simulation failed on ${name} ${c.asset} (withFeePayer=${c.withFeePayer}): ${failure}`);
    }

    console.log(`  ${name} ${c.asset} (fee_payer=${c.withFeePayer}): ok`);
  }

  console.log(`All ${name} simulations passed successfully.`);
}

main().catch((err) => {
  console.error('MainNet simulation failed:', err);
  process.exit(1);
});
