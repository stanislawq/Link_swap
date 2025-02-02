from web3 import Web3
import json
import random


web3 = Web3(Web3.HTTPProvider("https://rpc.api.lisk.com"))
pair_address = "0xD501d4E381491F64274Cc65fdec32b47264a2422"
pair_abi_path = "abi/uniswapv3_abi.json"


def load_abi(file_path):
    with open(file_path, 'r') as file:
        abi = json.load(file)
    return abi


def get_slot0(pair_address, abi, web3):
    pair_contract = web3.eth.contract(address=pair_address, abi=abi)
    slot0 = pair_contract.functions.slot0().call()
    sqrt_price_x96 = slot0[0]
    print(f"{sqrt_price_x96}")
    return sqrt_price_x96


def calculate_min_output(sqrt_price_x96, amount_eth_wei, slippage_percent):
    price_in_x96 = (sqrt_price_x96 ** 2) / (2 ** 192)
    print(f"X96 Price: {price_in_x96}")
    min_output = amount_eth_wei * price_in_x96 * (1 - slippage_percent / 100)
    print(f"Min output before hex: {min_output}")

    min_output_hex = hex(int(min_output))
    print(f"Min value: {min_output_hex}")
    return min_output_hex


pair_abi = load_abi(pair_abi_path)

random_eth_amount = round(random.uniform(0.000003, 0.000015), 18)
amount_eth_wei = Web3.to_wei(random_eth_amount, 'ether')
print(f"Random ETH value: {random_eth_amount} ETH ({amount_eth_wei} wei)")
slippage_percent = 0.5

sqrt_price_x96 = get_slot0(pair_address, pair_abi, web3)

min_output_hex = calculate_min_output(sqrt_price_x96, amount_eth_wei, slippage_percent)

min_tokens_out_int = int(min_output_hex, 16)
min_tokens_out_hex = f"{min_tokens_out_int:064x}"
print(min_tokens_out_hex)
