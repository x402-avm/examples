"""LocalNet helper for doc examples: funds test accounts using LocalNet's KMD dispenser."""
from algosdk import account, kmd, transaction
from algosdk.v2client import algod

ALGOD_URL = "http://localhost:4001"
ALGOD_TOKEN = "a" * 64
KMD_URL = "http://localhost:4002"
KMD_TOKEN = "a" * 64
INDEXER_URL = "http://localhost:8980"

ALGOD = algod.AlgodClient(ALGOD_TOKEN, ALGOD_URL)


def dispenser() -> tuple[str, str]:
    """Retrieve the primary funded account from LocalNet's default unencrypted KMD wallet."""
    k = kmd.KMDClient(KMD_TOKEN, KMD_URL)
    w = next(x for x in k.list_wallets() if x["name"] == "unencrypted-default-wallet")
    h = k.init_wallet_handle(w["id"], "")
    addr = max(k.list_keys(h), key=lambda a: ALGOD.account_info(a)["amount"])
    return addr, k.export_key(h, "", addr)


def new_funded_account(algos: int = 10) -> tuple[str, str]:
    """Generate a new account and fund it with the specified amount of ALGO from the dispenser."""
    sk, addr = account.generate_account()
    d_addr, d_sk = dispenser()
    sp = ALGOD.suggested_params()
    txn = transaction.PaymentTxn(d_addr, sp, addr, algos * 1_000_000)
    ALGOD.send_transaction(txn.sign(d_sk))
    transaction.wait_for_confirmation(ALGOD, txn.get_txid(), 10)
    return sk, addr
