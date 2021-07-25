from core.optionchainset import OptionChainSet
from utils.tools import nr_days_between_dates

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

    def find_expiry(self, preferred_dte=2, allow0dte=False):
        """
        Return option chain with DTE closest to preferred_dte
        :param preferred_dte: preferred number of days to expiry
        :param allow0dte: allow or not 0 DTE options
        :return: the option chain closest to the required DTE, or None if none found
        """
        # Find an expiration with preferred DTE
        best_expiry = None
        closest_dte = None
        for expiration in self.get_option_expiries():
            expiration_dte = nr_days_between_dates(self.quotedate, expiration)
            if expiration_dte == 0 and not allow0dte:
                continue
            if best_expiry is None or abs(expiration_dte - preferred_dte) < abs(closest_dte - preferred_dte):
                best_expiry, closest_dte = expiration, expiration_dte
        return best_expiry

    def find_call_min_credit(self, preferred_credit, preferred_dte=2, allow0dte=False):
        """
        Find a call with DTE and Delta as close as possible to specs
        :param preferred_credit: preferred amount of credit we would like to receive
        :param preferred_dte: preferred number of days to expiry
        :param allow0dte: allow or not 0 DTE options
        :return: the call option closest to the required values, or None if none found
        """
        # Find an expiration with preferred DTE
        best_expiry = self.find_expiry(preferred_dte=preferred_dte, allow0dte=allow0dte)

        # Find an option with closest matching credit
        opchain = self.option_chains.get_option_chain_by_expiry(best_expiry)
        best_option = None
        closest_credit = None
        for option in opchain.options:
            if option.type == "CALL":
                if best_option is None or abs(option.midprice() - preferred_credit) < abs(closest_credit - preferred_credit):
                    best_option, closest_credit = option, option.midprice()

        return best_option

    def find_call(self, preferred_dte=2, preferred_delta=0.5, allow0dte=False):
        """
        Find a call with DTE and Delta as close as possible to specs
        :param preferred_dte: preferred number of days to expiry
        :param preferred_delta: preferred delta of the call (between 0 and 1)
        :param allow0dte: allow or not 0 DTE options
        :return: the call option closest to the required values, or None if none found
        """
        # Find an expiration with preferred DTE
        best_expiry = self.find_expiry(preferred_dte=preferred_dte, allow0dte=allow0dte)

        # Find an option with closest matching delta
        opchain = self.option_chains.get_option_chain_by_expiry(best_expiry)
        best_option = None
        closest_delta = None
        for option in opchain.options:
            if option.type == "CALL":
                if best_option is None or abs(option.delta - preferred_delta) < abs(
                        closest_delta - preferred_delta):
                    best_option, closest_delta = option, option.delta

        return best_option

    def find_put(self, preferred_dte=2, preferred_delta=0.5, allow0dte=False):
        """
        Find a put with DTE and Delta as close as possible to specs
        :param preferred_dte: preferred number of days to expiry
        :param preferred_delta: preferred delta of the call (between -1 and 0)
        :return: the put option closest to the required values, or None if none found
        """
        # Find an expiration with preferred DTE
        best_expiry = self.find_expiry(preferred_dte=preferred_dte, allow0dte=allow0dte)

        # Find an option with closest matching delta
        opchain = self.option_chains.get_option_chain_by_expiry(best_expiry)
        best_option = None
        closest_delta = None
        for option in opchain.options:
            if option.type == "PUT":
                if best_option is None or abs(option.delta - preferred_delta) < abs(
                        closest_delta - preferred_delta):
                    best_option, closest_delta = option, option.delta

        return best_option

    def get_option_by_symbol(self, symbol):
        """
        :param symbol: an option symbol (structure: "SPY:2021:07:02:CALL:425")
        :return: the option from the option_chains, or None if cannot be found
        """
        return self.option_chains.get_option_by_symbol(symbol)

    def get_option_expiries(self):
        """
        :return: list of option expirations
        """
        return self.option_chains.get_expiries()