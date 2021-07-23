from math import floor

from core.event import Event
from core.order import Order
from strategy.strategy import Strategy
from utils.tools import symbol_to_params

class LeveragedCoveredCall(Strategy):
    """
    A Covered Call strategy using deep ITM options as the long leg instead of owning stocks
    It imitates a poor man's covered call (PMCC): deep ITM call options for the long leg,
    shorter expiry covered calls for the short leg.
    """
    def __init__(self, params):
        super().__init__()
        self.long_dte = params.get("longdte", 30)
        self.long_delta = params.get("longdelta", 0.9)
        self.short_dte = params.get("shortdte", 3)
        self.short_delta = params.get("shortdelta", 0.3)

    def handle_event(self, open_positions, totalcash, totalvalue, event: Event):
        orders = []

        long_position_present = False
        short_position_present = False
        for (symbol, qty) in open_positions:
            if qty > 0:
                # We have a long position present
                ticker, option_expiry, option_type, strike = symbol_to_params(symbol)
                if event.quotedate >= option_expiry:
                    # Close current long position
                    close_order = Order(-qty, symbol)
                    orders.append(close_order)
                else:
                    long_position_present = True
            else:
                # We have a short position present
                ticker, option_expiry, option_type, strike = symbol_to_params(symbol)
                if event.quotedate >= option_expiry or not long_position_present:
                    # Close current short position
                    close_order = Order(-qty, symbol)
                    orders.append(close_order)
                else:
                    short_position_present = True

        if not long_position_present:
            # Buy as many long contracts as we can afford
            best_option = event.find_call(preferred_dte=self.long_dte, preferred_delta=self.long_delta)
            self.buy_qty = floor(totalvalue / best_option.midprice())

            order = Order(self.buy_qty, best_option.symbol)
            orders.append(order)

        if not short_position_present:
            # Write covered calls against short position
            best_option = event.find_call(preferred_dte=self.short_dte, preferred_delta=self.short_delta)
            order = Order(-self.buy_qty, best_option.symbol)
            orders.append(order)

        return orders

    def take_assignment(self):
        return False

    def get_unique_id(self):
        return "LeveragedCoveredCall(LongDelta:{};LongDTE:{};ShortDelta:{};ShortDTE:{})". \
            format(self.long_delta, self.long_dte, self.short_delta, self.short_dte)
