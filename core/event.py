from core.optionchainset import OptionChainSet

class Event:
    """
    A wrapper class to represent a point in time, with all the raw data associated with it.

    To keep things simple, an Event is assumed to stand for a daily price update.
    Otherwise, it gets tricky with different UNIX timestamps for different options.
    We can figure out a way later to extend it to other time granularities (ie: 15 mins. 1h, etc)

    """
    def __init__(self, ticker, quotedate, price, option_chains: OptionChainSet):
        """
        :param ticker: ticker string of the underlying ("SPY", "QQQ", ...)
        :param quotedate: date string (YYYY-MM-DD) when the quote was taken, as used in the DB
        :param price: price of the underlying at the time the data was fetched
        :param option_chains: a set of all option chains
        """
        self.ticker = ticker
        self.quotedate = quotedate
        self.price = price
        self.option_chains = option_chains

    def get_option_by_symbol(self, symbol):
        """
        :param symbol: an option symbol (structure: "SPY:2021:07:02:CALL:425")
        :return: the option from the option_chains, or None if cannot be found
        """
        return self.option_chains.get_option_by_symbol(symbol)