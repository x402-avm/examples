/**
 * Verification script for browser_paywall tutorial.
 *
 * Exercises the identical x402 client workflow and library functions as app.js
 * against the FastAPI server on port 9232.
 *
 * Note: The browser page itself is not run in this automated verification;
 * this script executes the identical client flow using Node.js.
 *
 * How to run:
 *   node verify.mjs
 */
import algosdk from 'algosdk';
import { decodePaymentRequired, payForRequirement } from 'x402-avm-js';

const ALGOD_URL = 'http://127.0.0.1';
const ALGOD_PORT = 4001;
const ALGOD_TOKEN = 'a'.repeat(64);
const KMD_URL = 'http://127.0.0.1';
const KMD_PORT = 4002;
const KMD_TOKEN = 'a'.repeat(64);
const SERVER_URL = 'http://127.0.0.1:9232/api/premium';

const algodClient = new algosdk.Algodv2(ALGOD_TOKEN, ALGOD_URL, ALGOD_PORT);

async function getDispenser() {
  const kmdClient = new algosdk.Kmd(KMD_TOKEN, KMD_URL, KMD_PORT);
  const wallets = (await kmdClient.listWallets()).wallets;
  const defaultWallet = wallets.find((w) => w.name === 'unencrypted-default-wallet');
  const handle = (await kmdClient.initWalletHandle(defaultWallet.id, '')).wallet_handle_token;
  const keys = (await kmdClient.listKeys(handle)).addresses;

  let maxBalance = 0n;
  let dispenserAddr = keys[0];
  for (const addr of keys) {
    const info = await algodClient.accountInformation(addr).do();
    const bal = BigInt(info.amount);
    if (bal > maxBalance) {
      maxBalance = bal;
      dispenserAddr = addr;
    }
  }

  const exportResp = await kmdClient.exportKey(handle, '', dispenserAddr);
  return { address: dispenserAddr, privateKey: exportResp.private_key };
}

async function createFundedAccount(algos = 5) {
  const account = algosdk.generateAccount();
  const dispenser = await getDispenser();
  const sp = await algodClient.getTransactionParams().do();
  const txn = algosdk.makePaymentTxnWithSuggestedParamsFromObject({
    sender: dispenser.address,
    receiver: account.addr,
    amount: algos * 1_000_000,
    suggestedParams: sp,
  });

  const signed = txn.signTxn(dispenser.privateKey);
  const sendRes = await algodClient.sendRawTransaction(signed).do();
  const txId = sendRes.txid || sendRes.txId;
  await algosdk.waitForConfirmation(algodClient, txId, 10);
  return account;
}

async function main() {
  console.log('--- Browser Paywall Verification (Node.js) ---');
  console.log('Note: The browser page itself is not run; this script tests the exact x402 functions used in app.js.\n');

  console.log('1. Generating funded buyer account on LocalNet...');
  const buyer = await createFundedAccount(5);
  const buyerAddr = buyer.addr.toString ? buyer.addr.toString() : buyer.addr;
  const initialInfo = await algodClient.accountInformation(buyerAddr).do();
  const initialBalance = Number(initialInfo.amount);
  console.log(`Buyer account: ${buyerAddr}`);
  console.log(`Initial balance: ${initialBalance} microALGO (${initialBalance / 1_000_000} ALGO)`);

  console.log('\n2. Sending initial unauthenticated request to GET /api/premium ...');
  const res1 = await fetch(SERVER_URL);
  console.log(`Received status: HTTP ${res1.status}`);

  if (res1.status !== 402) {
    throw new Error(`Expected HTTP 402 Payment Required, got ${res1.status}`);
  }

  const payReqHeader = res1.headers.get('payment-required');
  if (!payReqHeader) {
    throw new Error('Server 402 response did not include payment-required header');
  }

  console.log('Decoded PAYMENT-REQUIRED header...');
  const paymentRequired = decodePaymentRequired(payReqHeader);
  const requirement = paymentRequired.accepts[0];
  console.log(`- Scheme: ${requirement.scheme}`);
  console.log(`- Price: ${requirement.amount} microALGO (asset: ${requirement.asset})`);
  console.log(`- Pay To: ${requirement.payTo}`);
  console.log(`- Network: ${requirement.network}`);

  console.log('\n3. Building and signing exact AVM payment group with x402-avm-js...');
  const signTxnsCallback = async (unsignedBytesList, indexes) => {
    return unsignedBytesList.map((bytes, idx) => {
      if (indexes.includes(idx)) {
        const decoded = algosdk.decodeUnsignedTransaction(bytes);
        return decoded.signTxn(buyer.sk);
      }
      return null;
    });
  };

  const paymentSignature = await payForRequirement(
    paymentRequired,
    buyerAddr,
    algodClient,
    signTxnsCallback
  );
  console.log('Generated PAYMENT-SIGNATURE header.');

  console.log('\n4. Retrying request with PAYMENT-SIGNATURE header...');
  const res2 = await fetch(SERVER_URL, {
    headers: {
      'payment-signature': paymentSignature,
    },
  });

  console.log(`Received status: HTTP ${res2.status}`);
  if (res2.status !== 200) {
    const errorBody = await res2.text();
    throw new Error(`Expected HTTP 200 OK after payment, got ${res2.status}: ${errorBody}`);
  }

  const unlockedData = await res2.json();
  console.log('Unlocked content:');
  console.log(JSON.stringify(unlockedData, null, 2));

  console.log('\n5. Verifying on-chain balance change...');
  // Wait a short moment for settlement confirmation
  await new Promise((r) => setTimeout(r, 1500));
  const finalInfo = await algodClient.accountInformation(buyerAddr).do();
  const finalBalance = Number(finalInfo.amount);
  const balanceDrop = initialBalance - finalBalance;
  console.log(`Final balance: ${finalBalance} microALGO`);
  console.log(`Balance drop: ${balanceDrop} microALGO (price: ${requirement.amount} microALGO)`);

  if (balanceDrop < Number(requirement.amount)) {
    throw new Error(`Expected balance drop of at least ${requirement.amount}, got ${balanceDrop}`);
  }

  console.log('\n=== VERIFICATION SUCCESS: HTTP 200 received and balance drop confirmed! ===');
}

main().catch((err) => {
  console.error('Verification failed:', err);
  process.exit(1);
});
