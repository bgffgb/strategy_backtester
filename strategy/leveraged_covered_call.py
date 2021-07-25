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
        super().__init__(params)
        self.long_dte = params.get("longdte", 30)
        self.long_delta = params.get("longdelta", 0.9)
        self.short_dte = params.get("shortdte", 3)
        self.short_delta = params.get("shortdelta", 0.3)
        self.closeonprofit = params.get("closeonprofit", 1)
        self.creditroll = params.get("creditroll", 0)
        self.short_pos_value = 0

    def handle_event(self, open_positions, totalcash, totalvalue, event: Event):
        orders = []

        long_position_present = False
        short_position_present = False
        min_roll_price = None
        
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
                close_short_position = False

                # Close short position if we don't have a long leg or it is expiring
                if event.quotedate >= option_expiry or not long_position_present:
                    close_short_position = True

                # Close short position if profit target reached

                curr_option = event.get_option_by_symbol(symbol)
                if curr_option:
                    current_short_pos_value = event.get_option_by_symbol(symbol).midprice() * qty
                    if self.short_pos_value != 0 and current_short_pos_value / self.short_pos_value <= 1 - self.closeonprofit:
                        close_short_position = True

                # Check if we need to roll for credit
                if curr_option and close_short_position and self.creditroll == 1:
                    min_roll_price = curr_option.midprice()

                if close_short_position:
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
            # Write covered calls against long position
            best_option = event.find_call(preferred_dte=self.short_dte, preferred_delta=self.short_delta)
            if self.creditroll == 1 and min_roll_price and best_option.midprice() < min_roll_price:
                # Find an option that satisfies credit requirement
                best_option = event.find_call_min_credit(preferred_dte=self.short_dte, preferred_credit=min_roll_price)
            self.short_pos_value = -self.buy_qty * best_option.midprice()
            order = Order(-self.buy_qty, best_option.symbol)
            orders.append(order)

        return orders

    def take_assignment(self):
        return False

    def get_unique_id(self):
        return "LeveragedCoveredCall(LongDelta:{};LongDTE:{};ShortDelta:{};ShortDTE:{};CloseProfit:{};CreditRoll:{})". \
            format(self.long_delta, self.long_dte, self.short_delta, self.short_dte, self.closeonprofit, self.creditroll)
