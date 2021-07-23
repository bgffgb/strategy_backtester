from math import floor

from core.event import Event
from core.order import Order
from strategy.strategy import Strategy
from utils.tools import symbol_to_params


class Wheel(Strategy):
    """
    Wheel strategy
    Given a starting amount of cash, this strategy first writes cash secured puts (CSP), and if taking assignment of
    the shares, switches to writing covered calls (CC). If the shares are called away, it switches back to writing CSP.
    """
    def __init__(self, params):
        super().__init__()
        self.preferred_call_dte = params.get("calldte", 5)
        self.preferred_call_delta = params.get("calldelta", 0.3)
        self.preferred_put_dte = params.get("putdte", 5)
        self.preferred_put_delta = params.get("putdelta", -0.3)

    def handle_event(self, open_positions, totalcash, totalvalue, event: Event):
        orders = []
        if len(open_positions) == 0:
            # When no open positions, sell cash covered puts
            best_option = event.find_put(self.preferred_put_dte, self.preferred_put_delta)

            # Check how many contracts we can afford max, once premium is added
            self.buy_qty = floor(totalcash / (best_option.strike - best_option.midprice() / 100)) // 100

            order = Order(-self.buy_qty, best_option.symbol)
            orders.append(order)
        elif len(open_positions) == 1:
            for (symbol, qty) in open_positions:
                ticker, option_expiry, option_type, strike = symbol_to_params(symbol)
                if option_expiry is None:
                    # Open stock position, sell covered calls
                    best_option = event.find_call(self.preferred_call_dte, self.preferred_call_delta)
                    order = Order(-self.buy_qty, best_option.symbol)
                    orders.append(order)

        return orders

    def take_assignment(self):
        return True

    def get_unique_id(self):
        return "Wheel(CallDelta:{};CallDTE:{};PutDelta:{};PutDTE:{})".\
            format(self.preferred_call_delta, self.preferred_call_dte, self.preferred_put_delta, self.preferred_put_dte)