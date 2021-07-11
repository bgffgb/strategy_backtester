from core.event import Event
from core.order import Order
from strategy.strategy import Strategy


class BuyAndHold(Strategy):
    """
    Simple Buy and Hold strategy.
    Opens a position for 100 shares on the first event and ignores the rest.
    """
    def __init__(self, params):
        super().__init__()
        self.boughtstuff = False

    def handle_event(self, event: Event):
        if not self.boughtstuff:
            # When starting up, buy 100 units of the underlying ticker
            order = Order(100, event.ticker)
            return [order]

        # Just wait and hold, nothing to do...
        return []

    def get_unique_id(self):
        return "BuyAndHold"

