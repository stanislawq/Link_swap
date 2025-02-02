import json
from decimal import Decimal


class TokenAmount:
    def __init__(self, amount, decimals, wei):
        if wei:
            self.Wei: int = amount
            self.Ether: int = int(Decimal(str(amount)) / 10 ** decimals)
        else:
            self.Wei: int = int(Decimal(str(amount)) * 10 ** decimals)
            self.Ether: int = amount


def read_json(path: str, encoding=None):
    return json.load(open(path, encoding=encoding))
