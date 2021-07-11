import logging

from core.portfolio import  Portfolio
from utils.data_loader import events_generator
from strategy.buyandhold import BuyAndHold

logger = logging.getLogger(__name__)


def spawn_strategies(params):
    strategy_list = []
    if "strategy" in params:
        """
        Add initializaiton of new strategies here; map a string to their class;
        """
        if params["strategy"].lower() == "buyandhold":
            new_strat = BuyAndHold(params)
            strategy_list.append(new_strat)
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

        # Get strategies initialized
        self.strategy_list = spawn_strategies(test_params)

        # Initialize a portfolio for each of these strategies
        self.portfolio_list = [Portfolio() for _ in self.strategy_list]

    def run(self):
        for event in events_generator(ticker=self.ticker, fromdate=self.start_date, todate=self.end_date):
            logger.info("New event for {}, date {}".format(event.ticker, event.quotedate))

            for strategy, portfolio in zip(self.strategy_list, self.portfolio_list):
                # Take order decisions from strategy
                orders = strategy.handle_event(event)

                # Update portfolio holdings
                portfolio.update_portfolio(orders, event)
                logger.info("Strategy {} Portfolio Value {}".format(strategy.get_unique_id(), portfolio.get_net_value()))
