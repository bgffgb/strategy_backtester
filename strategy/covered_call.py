from math import floor

from core.event import Event
from core.order import Order
from strategy.strategy import Strategy
from utils.date_tools import nr_days_between_dates

class CoveredCall(Strategy):
    """
    Simple Covered Call strategy
    Opens a position for as many shares (multiple of 100x) as it can afford and sells covered calls against it
    """
    def __init__(self, params):
        super().__init__()
        self.preferred_dte = params.get("dte", 5)
        self.preferred_delta = params.get("delta", 0.3)

    def pick_covered_call(self, event):
        # Find an expiration with preferred DTE
        best_expiry = None
        closest_dte = None
        for expiration in event.get_option_expiries():
            expiration_dte = nr_days_between_dates(event.quotedate, expiration)
            if best_expiry is None or abs(expiration_dte - self.preferred_dte) < abs(closest_dte - self.preferred_dte):
                best_expiry, closest_dte = expiration, expiration_dte

        # Find an option with closest matching delta
        opchain = event.option_chains.get_option_chain_by_expiry(best_expiry)
        best_option = None
        closest_delta = None
        for option in opchain.options:
            if option.type == "CALL":
                if best_option is None or abs(option.delta - self.preferred_delta) < abs(
                        closest_delta - self.preferred_delta):
                    best_option, closest_delta = option, option.delta

        # Place order to short
        order = Order(-self.buy_qty / 100, best_option.symbol)
        return order

    def handle_event(self, open_positions, totalcash, event: Event):
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
            order = self.pick_covered_call(event)
            orders.append(order)

        # TODO: No option rolling right now; strategy lets them expire (and take the loss on expiry)

        return orders

    def get_unique_id(self):
        return "CoveredCall(Delta:"+str(self.preferred_delta)+";DTE:"+str(self.preferred_dte)+")"
