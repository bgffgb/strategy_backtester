import logging

from core.event import Event


logger = logging.getLogger(__name__)


class Portfolio:
    """
    Portfolio manager that handles:
    - buying/selling of positions
    - closing out options contracts that expired and updating the portfolio accordingly
    - storing the historical net asset value of the account over time
    - .. calculating returns, max drawdown, etc

    Positions held are identified by their symbol, which is either a ticker (like "SPY") or an option symbol (like
    "SPY:2021:07:02:CALL:425")

    The structure of the portfolio class:
    - holdings_qty: maps symbols to quantity held
    - holdings_expiry_date: maps symbols to their expiry date (for options), or None for underlying
    - holdings_quote_date: maps symbols to the latest price quote date on record
    - holdings_last_price_info: maps symbols to the latest known price
    """
    def __init__(self):
        self.cash = 0
        self.holdings_qty = {}
        self.holdings_expiry_date = {}
        self.holdings_quote_date = {}
        self.holdings_last_price_info = {}

    def __str__(self):
        """
        :return: easily readable string of the portfolio status
        """
        msg = "Portfolio holdings:\n Cash: {}\n".format(self.cash)
        for symbol in self.holdings_qty.keys():
            qty = self.holdings_qty[symbol]
            val = qty * self.holdings_last_price_info[symbol]
            msg += "Pos: {} Symbol: {} Value: {}\n".format(qty, symbol, val)
        return msg

    def get_net_value(self):
        """
        :return: net liquidation value of the portfolio
        """
        net_value = self.cash
        for symbol in self.holdings_qty.keys():
            net_value += self.holdings_qty[symbol] * self.holdings_last_price_info[symbol]
        return net_value

    def adjust_holdings(self, symbol, qty, price):
        """
        Add/Update quantity owned of different products by qty number specified
        :param symbol: symbol of the product (option symbol or ticker for underlying)
        :param qty: amount to adjust qty owned by; positive values to go long, negative ones to go short
        :param price: price to be paid for the product
        """

        cash_cost = qty * price
        self.cash -= cash_cost

        if symbol not in self.holdings_qty:
            # Add new entry about this holding
            self.holdings_qty[symbol] = 0
        self.holdings_qty[symbol] += qty

    def update_data(self, event : Event):
        for symbol in self.holdings_qty.keys():
            if symbol == event.ticker:
                self.holdings_last_price_info[symbol] = event.price
                self.holdings_quote_date[symbol] = event.quotedate
                self.holdings_expiry_date[symbol] = None
            else:
                option = event.get_option_by_symbol(symbol)
                if option:
                    self.holdings_last_price_info[symbol] = option.midprice()
                    self.holdings_quote_date[symbol] = option.quotedate
                    self.holdings_expiry_date[symbol] = option.expiry

    def update_portfolio(self, order_list, event: Event):
        """
        With each new event, the portfolio class:
         - updates holdings based on new incoming orders
         - update info on prices on record for all portfolio holdings
         - handles expired option contracts/assignments

        :param order_list: list of new orders to be executed
        :param event: an Event class with price data
        """
        # Update holdings
        for order in order_list:
            if order.symbol == event.ticker:
                # It's an order for the underlying
                self.adjust_holdings(symbol=order.symbol, qty=order.qty, price=event.price)
            else:
                # It's an option contract
                option = event.get_option_by_symbol(order.symbol)
                if option:
                    # Only execute if not None
                    self.adjust_holdings(symbol=order.symbol, qty=order.qty, price=option.midprice())
                else:
                    logger.info("Could not execute order, cannot find option with symbol {}".format(order.symbol))

        # Update product quote dates/last prices
        self.update_data(event)

        # Handle expired options
        # TODO: actually implement it...



