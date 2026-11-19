"""HTTPX client that pays x402 paywalls automatically on LocalNet.

Start fastapi_paywall.py (port 9211) or flask_paywall.py (9212) first, then:

    python localnet/httpx_client.py [--url http://127.0.0.1:9211/weather]
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from x402 import x402Client
from x402.http.clients.httpx import wrapHttpxWithPayment
from x402_algorand import PayerAvmSigner
from x402_algorand.exact import register_exact_avm_client

from _localnet import ALGOD, ALGOD_TOKEN, ALGOD_URL, new_funded_account


async def main(url: str) -> None:
    sk, addr = new_funded_account(5)
    before = ALGOD.account_info(addr)["amount"]

    client = x402Client()  # default spend controls allow ALGO up to 1,000,000 microALGO
    register_exact_avm_client(
        client, PayerAvmSigner.from_private_key(sk), algod_url=ALGOD_URL, algod_token=ALGOD_TOKEN
    )
    async with wrapHttpxWithPayment(client) as http:
        response = await http.get(url, timeout=30.0)
    print(response.status_code, response.json())

    spent = before - ALGOD.account_info(addr)["amount"]
    assert response.status_code == 200 and spent == 10_000, (response.status_code, spent)
    print(f"Paid exactly {spent} microALGO.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:9211/weather")
    asyncio.run(main(parser.parse_args().url))
