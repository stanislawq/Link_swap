import sqlite3
import random
import time
import json
from client import Client
from web3 import Web3

lsk_token_address = Web3.to_checksum_address("0xac485391EB2d7D88253a7F1eF18C37f4242D1A24")
lsk_token_abi_path = "abi/lsk_abi.json"


def get_erc20_balance(web3, wallet_address, token_address, token_abi):
    token_contract = web3.eth.contract(address=token_address, abi=token_abi)
    balance = token_contract.functions.balanceOf(Web3.to_checksum_address(wallet_address)).call()
    decimals = token_contract.functions.decimals().call()
    return balance / (10 ** decimals)


def get_wallet_address_from_private_key(web3, private_key):
    account = web3.eth.account.from_key(private_key)
    return account.address


def load_abi(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


def get_slot0(pair_address, abi, web3):
    pair_contract = web3.eth.contract(address=pair_address, abi=abi)
    slot0 = pair_contract.functions.slot0().call()
    return slot0[0]


def calculate_min_output(sqrt_price_x96, amount_wei, slippage_percent, is_eth_to_token=True):
    price = (sqrt_price_x96 ** 2) / (2 ** 192) if is_eth_to_token else (2 ** 192) / (sqrt_price_x96 ** 2)
    min_output = amount_wei * price * (1 - slippage_percent / 100)
    return hex(int(min_output))


def calculate_min_output1(sqrt_price_x96, amount_lsk_wei, slippage_percent):
    min_output_eth = amount_lsk_wei * sqrt_price_x96 * (1 - slippage_percent / 100)
    min_output_hex = hex(int(min_output_eth))
    return min_output_hex


def get_accounts(db_path):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute("SELECT private_key FROM accounts")
    accounts = [row[0] for row in cursor.fetchall()]
    connection.close()
    return accounts


def update_balance(db_path, private_key, balance):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE accounts
        SET balance = ?
        WHERE private_key = ?
    """, (float(round(balance, 5)), private_key))
    connection.commit()
    connection.close()


def main():
    DB_PATH = "accounts.db"
    RPC_URL = "https://rpc.api.lisk.com"
    CHAIN_ID = 1135
    ROUTER_ADDRESS = "0x447B8E40B0CdA8e55F405C86bC635D02d0540aB8"
    PAIR_ADDRESS = "0xD501d4E381491F64274Cc65fdec32b47264a2422"
    PAIR_ABI_PATH = "abi/uniswapv3_abi.json"
    SLIPPAGE_PERCENT = 0.5
    MIN_SWAP_AMOUNT = 0.000003
    tx_count = 0
    web3 = Web3(Web3.HTTPProvider(RPC_URL))
    pair_abi = load_abi(PAIR_ABI_PATH)
    accounts = get_accounts(DB_PATH)
    if not accounts:
        print("No accounts found in the database.")
        return

    for account_index, private_key in enumerate(accounts, start=1):
        print("=============================================================")
        print(f"Processing account {account_index}/{len(accounts)}")
        client = Client(private_key, RPC_URL, CHAIN_ID, ROUTER_ADDRESS)

        for iteration in range(20):
            try:
                eth_balance = client.get_balance()
                update_balance(DB_PATH, private_key, eth_balance)
                print(f"ETH Balance: {eth_balance}")
                time.sleep(1.5)

                if eth_balance < MIN_SWAP_AMOUNT:
                    print("Insufficient ETH balance.")
                    break

                max_swap = min(random.uniform(0.000003, 0.00001), eth_balance)
                eth_amount_wei = Web3.to_wei(max_swap, 'ether')
                eth_amount_hex = f"{eth_amount_wei:064x}"

                sqrt_price_x96 = get_slot0(PAIR_ADDRESS, pair_abi, web3)
                min_output_hex = calculate_min_output(sqrt_price_x96, eth_amount_wei, SLIPPAGE_PERCENT)
                min_tokens_out_int = int(min_output_hex, 16)
                min_tokens_out_hex = f"{min_tokens_out_int:064x}"
                tx_hash = client.swap_eth_to_token1(max_swap, eth_amount_hex, min_tokens_out_hex,
                                                    int(time.time()) + 600)
                if not client.verify_tx(tx_hash):
                    continue

                time.sleep(random.uniform(10, 25))
                print("\n-------------------------------------------------------------\n")

                wallet_address = get_wallet_address_from_private_key(web3, private_key)
                pair_abi = load_abi(PAIR_ABI_PATH)
                lsk_token_abi = load_abi(lsk_token_abi_path)
                lsk_balance = get_erc20_balance(web3, wallet_address, lsk_token_address, lsk_token_abi)
                print(f"LSK Balance: {lsk_balance} LSK")
                if lsk_balance < MIN_SWAP_AMOUNT:
                    print("Not enough balance for further swaps.")
                    break

                amount_to_swap = float(lsk_balance) * 0.9
                amount_lsk_wei = Web3.to_wei(amount_to_swap, 'ether')
                amount_lsk_hex = f"{int(amount_lsk_wei):064x}"

                sqrt_price_x96 = get_slot0(PAIR_ADDRESS, pair_abi, web3)
                price_in_x96 = 1 / ((sqrt_price_x96 ** 2) / (2 ** 192))

                min_output_hex = calculate_min_output1(price_in_x96, amount_lsk_wei, SLIPPAGE_PERCENT)

                min_tokens_out_int = int(min_output_hex, 16)
                min_tokens_out_hex = f"{min_tokens_out_int:064x}"

                tx_hash = client.swap_eth_to_token(amount_to_swap, amount_lsk_hex, min_tokens_out_hex,
                                                   int(time.time()) + 600)

                if client.verify_tx(tx_hash):
                    tx_count += 1
                    print(f"\nTransaction count: {tx_count}")
                else:
                    print("Swap not complete")

                print("=============================================================")
                sleep_time = random.uniform(6, 25)
                time.sleep(sleep_time)

            except Exception as e:
                print(f"Error: {e}")
                time.sleep(15)
                continue


if __name__ == "__main__":
    main()
