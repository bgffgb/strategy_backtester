from math import floor

from core.event import Event
from core.optionchain import OptionChain
from core.order import Order
from indicators.rnd import get_RND_distribution, Distribution
from strategy.strategy import Strategy

class RndStrategy(Strategy):
    """
    A strategy that buys/sells option spreads with high expected returns based on RND distribution
    Positions are closed out at expiry
    """
    def __init__(self, params):
        super().__init__()
        self.dte = params.get("dte", 5)
        self.possize = params.get("possize", 10)
        self.min_call_delta = params.get("mincalldelta", 0.3)
        self.max_call_delta = params.get("maxcalldelta", 0.7)
        self.min_put_delta = params.get("minputdelta", -0.7)
        self.max_put_delta = params.get("maxputdelta", -0.3)

        # Safety check, negative numbers can be confusing
        if self.min_put_delta > self.max_put_delta:
            self.min_put_delta, self.max_put_delta = self.max_put_delta, self.min_put_delta

    def get_option_profits(self, chain: OptionChain, distribution: Distribution):
        # Evaluate all option probabilities matching delta criterias
        option_returns = []
        for strike, op in chain.get_sorted_calls():
            if self.min_call_delta <= op.delta <= self.max_call_delta:
                ret = distribution.get_option_expected_return(op)
                perc = ret / op.midprice() * 100
                option_returns.append((abs(perc), perc, op))

        for strike, op in chain.get_sorted_puts():
            if self.min_put_delta <= op.delta <= self.max_put_delta:
                ret = distribution.get_option_expected_return(op)
                perc = ret / op.midprice() * 100
                option_returns.append((abs(perc), perc, op))

        return option_returns

    def handle_event(self, open_positions, totalcash, totalvalue, event: Event):
        orders = []
        best_expiry = event.find_expiry(preferred_dte=self.dte, allow0dte=False)
        chain = event.option_chains.get_option_chain_by_expiry(best_expiry)
        distribution = get_RND_distribution(chain)

        options_by_rnd_profit = self.get_option_profits(chain=chain, distribution=distribution)
        for i in range(min(5, len(options_by_rnd_profit))):
            _, perc, op = options_by_rnd_profit[i]
            possize = self.possize
            if perc < 0:
                possize = -self.possize
            orders.append(Order(qty=possize, symbol=op.symbol))

        return orders

    def take_assignment(self):
        return False

    def get_unique_id(self):
        return "RNDStrategy(DTE:{};Pos:{};CallDelta:{}-{};PutDelta:{}-{})".\
            format(self.dte, self.possize, self.min_call_delta, self.max_call_delta,
                   self.min_put_delta, self.max_put_delta)
