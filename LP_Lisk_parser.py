from web3 import Web3
import json

web3 = Web3(Web3.HTTPProvider("https://rpc.api.lisk.com"))
pair_address = "0xD501d4E381491F64274Cc65fdec32b47264a2422"
pair_abi_path = "abi/uniswapv3_abi.json"
private_key = "private_key"
lsk_token_address = Web3.to_checksum_address("0xac485391EB2d7D88253a7F1eF18C37f4242D1A24")
lsk_token_abi_path = "abi/lsk_abi.json"


def load_abi(file_path):
    with open(file_path, 'r') as file:
        abi = json.load(file)
    return abi


def get_slot0(pair_address, abi, web3):
    pair_contract = web3.eth.contract(address=pair_address, abi=abi)
    slot0 = pair_contract.functions.slot0().call()
    sqrt_price_x96 = slot0[0]
    print(f"Sqrt Price X96: {sqrt_price_x96}")
    return sqrt_price_x96


def get_wallet_address_from_private_key(web3, private_key):
    account = web3.eth.account.from_key(private_key)
    return account.address


def get_erc20_balance(web3, wallet_address, token_address, token_abi):
    token_contract = web3.eth.contract(address=token_address, abi=token_abi)
    balance = token_contract.functions.balanceOf(Web3.to_checksum_address(wallet_address)).call()
    decimals = token_contract.functions.decimals().call()
    return balance / (10 ** decimals)


def calculate_min_output(sqrt_price_x96, amount_lsk_wei, slippage_percent):
    min_output_eth = amount_lsk_wei * sqrt_price_x96 * (1 - slippage_percent / 100)
    print(f"Min ETH output before hex: {min_output_eth}")
    min_output_hex = hex(int(min_output_eth))
    print(f"Min ETH output (hex): {min_output_hex}")
    return min_output_hex


try:

    wallet_address = get_wallet_address_from_private_key(web3, private_key)
    print(f"Wallet address: {wallet_address}")

    pair_abi = load_abi(pair_abi_path)

    lsk_token_abi = load_abi(lsk_token_abi_path)

    lsk_balance = get_erc20_balance(web3, wallet_address, lsk_token_address, lsk_token_abi)
    print(f"Current LSK Balance: {lsk_balance} LSK")

    amount_to_swap = lsk_balance
    amount_lsk_wei = Web3.to_wei(amount_to_swap, 'ether')
    print(f"Using {amount_to_swap} LSK ({amount_lsk_wei} wei) for swap")

    slippage_percent = 0.5

    sqrt_price_x96 = get_slot0(pair_address, pair_abi, web3)
    price_in_x96 = 1 / ((sqrt_price_x96 ** 2) / (2 ** 192))
    print(price_in_x96)

    min_output_hex = calculate_min_output(price_in_x96, amount_lsk_wei, slippage_percent)

    min_tokens_out_int = int(min_output_hex, 16)
    min_tokens_out_hex = f"{min_tokens_out_int:064x}"
    print(f"Min tokens output in hex format: {min_tokens_out_hex}")

except Exception as e:
    print(f"An error occurred: {e}")
