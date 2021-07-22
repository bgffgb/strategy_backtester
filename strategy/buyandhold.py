from math import floor

from core.event import Event
from core.order import Order
from strategy.strategy import Strategy


class BuyAndHold(Strategy):
    """
    Simple Buy and Hold strategy.
    Opens a position for as many shares as it can afford and never seels :)
    """
    def __init__(self, params):
        super().__init__()

    def handle_event(self, open_positions, totalcash, event: Event):
        if len(open_positions) == 0:
            # When starting up, buy as many of the underlying ticker as possible
            buy_qty = floor(totalcash / event.price)
            order = Order(buy_qty, event.ticker)
            return [order]

        # Just wait and hold, nothing to do...
        return []

    def take_assignment(self):
        return False

    def get_unique_id(self):
        return "BuyAndHold"