from math import floor

from core.event import Event
from core.order import Order
from strategy.strategy import Strategy
from utils.tools import symbol_to_params


class DeltaNeutral(Strategy):
    """
    A semi-delta neutral strategy using a four legged strategy:
    - long deep ITM Put + Call legs
    - short OTM Put + Call legs of shorter expiry
    """
    def __init__(self, params):
        super().__init__(params)
        self.long_dte = params.get("longdte", 30)
        self.long_delta = params.get("longdelta", 0.9)
        self.short_dte = params.get("shortdte", 3)
        self.short_delta = params.get("shortdelta", 0.3)
        self.closeonprofit = params.get("closeonprofit", 1)
        self.short_put_value = 0
        self.short_call_value = 0

    def handle_event(self, open_positions, totalcash, totalvalue, event: Event):
        orders = []
        long_position_present = False
        short_put_present = False
        short_call_present = False
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

        for (symbol, qty) in open_positions:
            if qty < 0:
                # We have a short position present
                ticker, option_expiry, option_type, strike = symbol_to_params(symbol)
                close_short_position = False

                if event.quotedate >= option_expiry or not long_position_present:
                    close_short_position = True

                curr_option = event.get_option_by_symbol(symbol)
                if curr_option:
                    current_short_pos_value = event.get_option_by_symbol(symbol).midprice() * qty
                    if "CALL" in symbol:
                        refval = self.short_call_value
                    if "PUT" in symbol:
                        refval = self.short_put_value
                    if refval != 0 and current_short_pos_value / refval <= 1 - self.closeonprofit:
                        close_short_position = True

                if close_short_position:
                    # Close current short position
                    close_order = Order(-qty, symbol)
                    orders.append(close_order)
                else:
                    if "CALL" in symbol:
                        short_call_present = True
                    if "PUT" in symbol:
                        short_put_present = True

        if not long_position_present:
            # Buy as many long contracts as we can afford
            best_call = event.find_call(preferred_dte=self.long_dte, preferred_delta=self.long_delta)
            best_put = event.find_put(preferred_dte=self.long_dte, preferred_delta=-self.long_delta)

            self.buy_qty = floor(totalvalue / (best_call.midprice() + best_put.midprice()))

            order = Order(self.buy_qty, best_call.symbol)
            orders.append(order)
            order = Order(self.buy_qty, best_put.symbol)
            orders.append(order)

        if not short_call_present:
            # Write covered options against long positions
            best_call = event.find_call(preferred_dte=self.short_dte, preferred_delta=self.short_delta)
            self.short_call_value = -self.buy_qty * best_call.midprice()
            order = Order(-self.buy_qty, best_call.symbol)
            orders.append(order)

        if not short_put_present:
            # Write covered options against long positions
            best_put = event.find_put(preferred_dte=self.short_dte, preferred_delta=-self.short_delta)
            self.short_put_value = -self.buy_qty * best_put.midprice()
            order = Order(-self.buy_qty, best_put.symbol)
            orders.append(order)

        return orders

    def take_assignment(self):
        return False

    def get_unique_id(self):
        return "DeltaNeutral(LongDelta:{};LongDTE:{};ShortDelta:{};ShortDTE:{};CloseProfit:{})". \
            format(self.long_delta, self.long_dte, self.short_delta, self.short_dte, self.closeonprofit)
