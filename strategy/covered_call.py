from math import floor

from core.event import Event
from core.order import Order
from strategy.strategy import Strategy
from utils.tools import symbol_to_params

class CoveredCall(Strategy):
    """
    Simple Covered Call strategy
    Opens a position for as many shares (multiple of 100x) as it can afford and sells covered calls against it
    """
    def __init__(self, params):
        super().__init__(params)
        self.preferred_dte = params.get("dte", 5)
        self.preferred_delta = params.get("delta", 0.3)

    def handle_event(self, open_positions, totalcash, totalvalue, event: Event):
        orders = []
        if len(open_positions) == 0:
            # When starting up, buy as many of the underlying ticker as possible
            self.buy_qty = floor(totalcash / event.price)
            # Make the order a multiple of 100
            self.buy_qty = (self.buy_qty // 100) * 100
            order = Order(self.buy_qty, event.ticker)
            orders.append(order)

        # Sell covered calls against position
        if len(open_positions) <= 1:
            # No open option positions currently, sell covered calls
            best_option = event.find_call(self.preferred_dte, self.preferred_delta)
            order = Order(-self.buy_qty / 100, best_option.symbol)
            orders.append(order)

        else:
            for (symbol, qty) in open_positions:
                ticker, option_expiry, option_type, strike = symbol_to_params(symbol)
                # Check if we need to roll covered calls further out
                if option_type == "CALL" and event.quotedate >= option_expiry:
                    # Only roll out if call is in the money
                    if strike <= event.price:
                        # Close current position
                        close_order = Order(-qty, symbol)
                        orders.append(close_order)

                        # Open new one further out
                        best_option = event.find_call(self.preferred_dte, self.preferred_delta)
                        open_order = Order(qty, best_option.symbol)
                        orders.append(open_order)

        return orders

    def take_assignment(self):
        return True

    def get_unique_id(self):
        return "CoveredCall(Delta:"+str(self.preferred_delta)+";DTE:"+str(self.preferred_dte)+")"
