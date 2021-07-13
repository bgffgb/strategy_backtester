class Order:
    def __init__(self, qty, symbol):
        """
        Wrapper class for structured orders
        :param qty: positive amounts: buy/long; negative amounts: sell/short
        :param symbol: ticker for underlying; option symbol for options
        """
        self.qty = qty
        self.symbol = symbol

    def __str__(self):
        return "({},{})".format(self.symbol, self.qty)