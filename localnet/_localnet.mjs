// LocalNet helper for the JavaScript examples: algod client and KMD-dispenser funding.
import algosdk from 'algosdk';
import { algodClient } from 'x402-avm-js';

const TOKEN = 'a'.repeat(64);
export const ALGOD_URL = 'http://localhost:4001';
export const algod = algodClient('localnet'); // port 4001 (needs x402-avm-js >= 0.4.1)
const kmd = new algosdk.Kmd(TOKEN, 'http://localhost', 4002);

/** Generate a new account and fund it with `algos` ALGO from the LocalNet dispenser. */
export async function newFundedAccount(algos = 10) {
  const wallet = (await kmd.listWallets()).wallets.find((w) => w.name === 'unencrypted-default-wallet');
  const handle = (await kmd.initWalletHandle(wallet.id, '')).wallet_handle_token;
  const balances = new Map();
  for (const addr of (await kmd.listKeys(handle)).addresses) {
    balances.set(addr, (await algod.accountInformation(addr).do()).amount);
  }
  const [dispenser] = [...balances].sort((a, b) => (b[1] > a[1] ? 1 : -1))[0];
  const { private_key } = await kmd.exportKey(handle, '', dispenser);

  const account = algosdk.generateAccount();
  const txn = algosdk.makePaymentTxnWithSuggestedParamsFromObject({
    sender: dispenser,
    receiver: account.addr,
    amount: algos * 1_000_000,
    suggestedParams: await algod.getTransactionParams().do(),
  });
  const { txid } = await algod.sendRawTransaction(txn.signTxn(private_key)).do();
  await algosdk.waitForConfirmation(algod, txid, 10);
  return { address: account.addr.toString(), sk: account.sk };
}

/** Wallet-style signer callback for x402-avm-js: signs the requested group indexes. */
export const signerFor = (sk) => async (txns, indexes) =>
  txns.map((bytes, i) => (indexes.includes(i) ? algosdk.decodeUnsignedTransaction(bytes).signTxn(sk) : null));
