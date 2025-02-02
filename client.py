from web3 import Web3
import os
from utils import read_json
import time

ABI_DIR = 'abi\\'
UNIVERSAL_ROUTER_ABI = os.path.join(ABI_DIR, 'erc20.json')


class Client:
    router_abi = read_json(UNIVERSAL_ROUTER_ABI)

    def __init__(self, private_key: str, rpc_url: str, chain_id: int, router_address: str):
        self.private_key = private_key
        self.rpc_url = rpc_url
        self.chain_id = chain_id
        self.router_address = Web3.to_checksum_address(router_address)
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.address = self.w3.eth.account.from_key(private_key).address

    def get_balance(self):
        balance = self.w3.eth.get_balance(self.address)
        return self.w3.from_wei(balance, 'ether')

    def get_erc20_balance(self, token_address, token_abi):
        token_contract = self.w3.eth.contract(address=token_address, abi=token_abi)
        balance = token_contract.functions.balanceOf(self.address).call()
        decimals = token_contract.functions.decimals().call()
        return balance / (10 ** decimals)

    def swap_eth_to_token1(self, amount_in_eth: float, amount_eth_hex: str, min_tokens_out_hex: str, deadline: int):
        print(f"{self.address} | Processing ETH to LSK swap...")
        time.sleep(1.5)
        try:
            contract = self.w3.eth.contract(address=self.router_address, abi=self.router_abi)
            inputs = [
                f"0000000000000000000000000000000000000000000000000000000000000002{amount_eth_hex}",
                f"000000000000000000000000{self.address[2:]}{amount_eth_hex}{min_tokens_out_hex}00000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002b4200000000000000000000000000000000000006000bb8ac485391eb2d7d88253a7f1ef18c37f4242d1a24000000000000000000000000000000000000000000"
            ]

            inputs = [bytes.fromhex(data) for data in inputs]

            commands = "0x0b00"

            txn = contract.functions.execute(
                commands,
                inputs,
                deadline
            ).build_transaction({
                'chainId': self.chain_id,
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'from': self.address,
                'value': Web3.to_wei(amount_in_eth, 'ether'),
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
            })

            signed_tx = self.w3.eth.account.sign_transaction(txn, private_key=self.private_key)

            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"{self.address} | Transaction hash: {'0x' + tx_hash.hex()}")
            time.sleep(1.5)

            return "0x" + tx_hash.hex()
        except ValueError as e:
            print(f"Error in ETH to Token swap: {e}")
            time.sleep(1.5)
            raise

    def swap_eth_to_token(self, amount_in_eth: float, amount_eth_hex: str, min_tokens_out_hex: str, deadline: int):
        print(f"{self.address} | Processing LSK to ETH swap... ")
        time.sleep(1.5)
        contract = self.w3.eth.contract(address=self.router_address, abi=self.router_abi)

        inputs1 = [
            f"0000000000000000000000000000000000000000000000000000000000000002{amount_eth_hex}{min_tokens_out_hex}00000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000002bac485391eb2d7d88253a7f1ef18c37f4242d1a24000bb84200000000000000000000000000000000000006000000000000000000000000000000000000000000",
            f"000000000000000000000000{self.address[2:]}{min_tokens_out_hex}"
        ]

        inputs = [bytes.fromhex(data) for data in inputs1]

        commands = "0x000c"

        txn = contract.functions.execute(
            commands,
            inputs,
            deadline
        ).build_transaction({
            'chainId': self.chain_id,
            'nonce': self.w3.eth.get_transaction_count(self.address),
            'from': self.address,
            'value': Web3.to_wei(amount_in_eth, 'wei'),
            'gas': 300000,
            'gasPrice': self.w3.eth.gas_price,
        })

        signed_tx = self.w3.eth.account.sign_transaction(txn, private_key=self.private_key)

        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"{self.address} | Transaction hash: {"0x" + tx_hash.hex()}")
        time.sleep(1.5)
        return "0x" + tx_hash.hex()

    def verify_tx(self, tx_hash):
        if not tx_hash:
            return False
        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            if receipt.status == 1:
                print(f"{self.address} | Transaction accepted!")
                time.sleep(1.5)
                return True
            else:
                print(f"{self.address} | Transaction declined")
                time.sleep(1.5)
                return False
        except Exception as e:
            print(f"{self.address} | Transaction error: {e}")
            time.sleep(1.5)
            return False
