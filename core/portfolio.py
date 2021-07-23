import logging

from core.event import Event
from strategy.strategy import Strategy
from utils.tools import symbol_to_params

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
    - holdings_quote_date: maps symbols to the latest price quote date on record
    - holdings_last_price_info: maps symbols to the latest known price
    - net_value_history: list of (date, netvalue) pairs in chronological order (historical portfolio net asset values)
    """
    def __init__(self, starting_cash, strategy: Strategy):
        self.cash = starting_cash
        self.strategy = strategy
        self.holdings_qty = {}
        self.holdings_quote_date = {}
        self.holdings_last_price_info = {}

        # Add a sole datapoint to mark the beginning of the portfolio (and it's net value at the start)
        self.net_value_history = [("start", self.cash)]

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

    def get_open_positions(self):
        """
        :return: a list of (symbol, quantity) pairs, representing current portfolio holdings
        """
        return self.holdings_qty.items()

    def get_performance(self):
        """
        :return: percentage up or down of the portfolio
        """
        initial_net_value = self.net_value_history[0][1]
        current_net_value = self.get_net_value()
        percentage_change = (current_net_value - initial_net_value) / initial_net_value
        return "{:.2f}%".format(percentage_change * 100)

    def get_max_drawdown(self):
        """
        :return: calculate max drawdown throughout the history of the portfolio
        """
        mdd = 0
        maxnetval = self.net_value_history[0][1]
        for (date, netval) in self.net_value_history:
            maxnetval = max(maxnetval, netval)
            if maxnetval != 0:
                mdd = min(mdd, (netval - maxnetval) * 1.0 / maxnetval)
        return "{:.2f}%".format(mdd * 100)

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

        if self.holdings_qty[symbol] == 0:
            # Remove this position
            self.holdings_qty.pop(symbol, None)
            self.holdings_quote_date.pop(symbol, None)
            self.holdings_last_price_info.pop(symbol, None)

    def update_data(self, event: Event):
        for symbol in self.holdings_qty.keys():
            if symbol == event.ticker:
                self.holdings_last_price_info[symbol] = event.price
                self.holdings_quote_date[symbol] = event.quotedate
            else:
                option = event.get_option_by_symbol(symbol)
                if option:
                    self.holdings_last_price_info[symbol] = option.midprice()
                    self.holdings_quote_date[symbol] = option.quotedate
        # Make sure to also update ticker price
        self.holdings_last_price_info[event.ticker] = event.price

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
        symbols = list(self.holdings_qty.keys())
        for symbol in symbols:
            ticker, option_expiry, option_type, strike = symbol_to_params(symbol)
            if option_expiry is not None:
                if event.quotedate >= option_expiry and event.ticker == ticker:
                    # Option expired/expires end of day
                    if self.strategy.take_assignment():
                        # Strategy takes assignment
                        if option_type == "CALL":
                            if strike < event.price:
                                # Call is in the money
                                # Add shares
                                logger.info("Call option {} took assignment (EOD stock price {})".
                                            format(symbol, event.price))
                                self.adjust_holdings(event.ticker, 100 * self.holdings_qty[symbol], strike)
                            else:
                                # Call expires worthless
                                logger.info("Call option {} expires worthless (EOD stock price {})".
                                            format(symbol, event.price))
                        else:
                            if strike > event.price:
                                # Put is in the money
                                # Add shares
                                logger.info("Put option {} took assignment (EOD stock price {})".
                                            format(symbol, event.price))
                                self.adjust_holdings(event.ticker, -100 * self.holdings_qty[symbol], strike)
                            else:
                                # Put expires worthless
                                logger.info("Put option {} expires worthless (EOD stock price {})".
                                            format(symbol, event.price))
                        # Remove options from holdings
                        self.adjust_holdings(symbol, -self.holdings_qty[symbol], 0)
                    else:
                        # Strategy closes positions before expiry
                        logger.info("Option {} closed out at price of {} (EOD stock price {})".
                                    format(symbol, self.holdings_last_price_info[symbol], event.price))
                        self.adjust_holdings(symbol, -self.holdings_qty[symbol], self.holdings_last_price_info[symbol])

        # Update historical net value
        self.net_value_history.append((event.quotedate, self.get_net_value()))



