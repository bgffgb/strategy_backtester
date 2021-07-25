import copy
import logging

from core.portfolio import  Portfolio
from utils.data_loader import events_generator
from strategy.buyandhold import BuyAndHold
from strategy.covered_call import CoveredCall
from strategy.delta_neutral import DeltaNeutral
from strategy.leveraged_covered_call import LeveragedCoveredCall
from strategy.rnd_strategy import RndStrategy
from strategy.wheel import Wheel

logger = logging.getLogger(__name__)


def strategy_from_params(params):
    """
    Add initializaiton of new strategies here; map a string to their class;
    :param params: parameters unique to the strategy
    :return: an initialized strategy
    """
    if params["strategy"].lower() == "buyandhold":
        return BuyAndHold(params)
    if params["strategy"].lower() == "coveredcall":
        return CoveredCall(params)
    if params["strategy"].lower() == "wheel":
        return Wheel(params)
    if params["strategy"].lower() == "leveragedcoveredcall":
        return LeveragedCoveredCall(params)
    if params["strategy"].lower() == "deltaneutral":
        return DeltaNeutral(params)
    if params["strategy"].lower() == "rndstrategy":
        return RndStrategy(params)


def get_all_permutations(original_params, params_to_generate, index, pos, permutation_list):
    N = len(index)
    if pos == len(index):
        # Create a deep copy of the original parameters
        param_cpy = copy.deepcopy(original_params)
        # Rewrite params according to current permutation
        for i in range(N):
            key, value = params_to_generate[i]
            param_cpy[key] = value[index[i]]
        permutation_list.append(param_cpy)
    else:
        # Generate all possible permutations
        L = len(params_to_generate[pos][1])
        for i in range(L):
            index[pos] = i
            get_all_permutations(original_params, params_to_generate, index, pos + 1, permutation_list)


def generate_permutations(params):
    params_to_generate = []
    for key, value in params.items():
        if type(value) == list:
            params_to_generate.append((key, value))

    N = len(params_to_generate)
    permutation_list = []
    get_all_permutations(params, params_to_generate, [0 for _ in range(N)], 0, permutation_list)
    return permutation_list


def spawn_strategies(params):
    """
    Spawn initialized strategies according to param specs
    :param params: dictionary of parameters (see Readme)
    :return: list of initialized strategies
    """
    strategy_list = []
    if "strategy" in params:
        # A single strategy is specified
        perm_list = generate_permutations(params)
        for param_version in perm_list:
            strategy_list.append(strategy_from_params(param_version))
    elif "strategies" in params:
        # Add multiple strategies for testing
        for strat_params in params["strategies"]:
            # Generate all permutations of array-style parameters
            perm_list = generate_permutations(strat_params)
            for param_version in perm_list:
                strategy_list.append(strategy_from_params(param_version))
    return strategy_list


class BackTestEngine:
    """
    The whole big backbone for backtesting.
    Given the test parameters, it will:
     - initialize the different strategies to be tested (and compared against each other)
     - initialize a portfolio for each of these strategies
     - load the options data from the DB
     - generate a series of chronological events
     - get the orders made by the strategies reacting to the events & update their portfolios
     - close down expired option positions on expiry (take assignment)
     - generate a final report in the end for each strategies performance
    """

    def __init__(self, test_params):
        """
        Do a whole lot of default initializations and sanity checking
        :param test_params: a json dictionary of test parameters; check sample.json for an example
        """
        # Start date
        logger.info("Setting up new Backtest run.")
        self.start_date = test_params.get("fromDate", None)
        if self.start_date is None:
            self.start_date = "2021-06-01"
            logger.info(
                "No 'fromDate' (start date) specified. Using default value of {} (inclusive)".format(self.start_date))
        else:
            logger.info("Start date set to {} (inclusive)".format(self.start_date))

        # End date
        self.end_date = test_params.get("toDate", None)
        if self.end_date is None:
            self.end_date = "2021-06-21"
            logger.info("No 'toDate' (end date) specified. Using default value of {} (exclusive)".format(self.end_date))
        else:
            logger.info("End date set to {} (exclusive)".format(self.end_date))

        # Ticker
        self.ticker = test_params.get("ticker", None)
        if self.ticker is None:
            self.ticker = "SPY"
            logger.info("No 'ticker' specified. Using default value of {}".format(self.ticker))

        # Set a starting cash amount, consistent across all strategies
        self.startcash = test_params.get("startcash", 1000000)

        # Get strategies initialized
        self.strategy_list = spawn_strategies(test_params)

        # Initialize a portfolio for each of these strategies
        self.portfolio_list = [Portfolio(starting_cash=self.startcash, strategy=strat) for strat in self.strategy_list]

    def run(self):
        """
        Run portfolio simulation over historical data for all the strategies
        :return: final summary result tuple of (performance, maxdrawdown, netvalue, strategy_id) sorted by performance
        """
        # Simulate events
        if len(self.strategy_list) == 0:
            logger.info("No strategies specified; nothing to test.")
        else:
            logger.info("Testing strategies: {}".format(",".join([s.get_unique_id() for s in self.strategy_list])))

        for event in events_generator(ticker=self.ticker, fromdate=self.start_date, todate=self.end_date):
            logger.info("New event for {}, date {}, price {}".format(event.ticker, event.quotedate, event.price))

            for strategy, portfolio in zip(self.strategy_list, self.portfolio_list):
                # Take order decisions from strategy
                orders = strategy.handle_event(open_positions=portfolio.get_open_positions(), totalcash=portfolio.cash,
                                               totalvalue=portfolio.get_net_value(), event=event)
                if len(orders) > 0:
                    logger.info("{} placed orders: {}".format(strategy.get_unique_id(), [str(o) for o in orders]))
                # Update portfolio holdings
                portfolio.update_portfolio(orders, event)
                logger.info("Strategy {} Portfolio Value {} Performance {:.2f}% MaxDrawdown {:.2f}%".
                            format(strategy.get_unique_id(), portfolio.get_net_value(),
                                   portfolio.get_performance(), portfolio.get_max_drawdown()))

        # Sort strategies by results and risk
        summary = []
        for strategy, portfolio in zip(self.strategy_list, self.portfolio_list):
            summary.append((portfolio.get_performance(), portfolio.get_max_drawdown(),
                            portfolio.get_net_value(), strategy.get_unique_id(), strategy))
        summary.sort(reverse=True)

        # Print final portfolio stats
        logger.info("Out of events! Final results")
        for perf, drawdown, netval, id, _ in summary:
            logger.info("Strategy {} Portfolio Value {} Performance {:.2f}% MaxDrawdown {:.2f}%".
                        format(id, netval, perf, drawdown))
        return summary