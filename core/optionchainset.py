from .optionchain import OptionChain


class OptionChainSet:
    """
    A set of all option chains, built from DB data
    """
    def __init__(self, ticker, option_list=None):
        """
        Construct the set of structured option chains form a list of queried options

        :param ticker: ticker string of the underlying ("SPY", "QQQ", ...)
        :param option_list: a list of Option classes to be added to the option chains (optional)
        """

        # Store options in a dictionary, using the expiry as a key
        self.ticker = ticker
        self.tot_options = 0
        self.option_chains_by_expiry = {}
        self.symbol_to_option = {}

        if option_list:
            for o in option_list:
                self.add_option(o)

    def add_option(self, o):
        # Just make sure option ticker matches the option chain we are building
        if o.ticker == self.ticker:
            expiry = o.expiry
            if expiry not in self.option_chains_by_expiry:
                # Create a new option chain for this expiry
                self.option_chains_by_expiry[expiry] = OptionChain(ticker=self.ticker, quotedate=o.quotedate)
            self.option_chains_by_expiry[expiry].add_option(o)
            self.tot_options += 1

            # For quick lookups, store option symbol -> option mapping
            self.symbol_to_option[o.symbol] = o

    def get_expiries(self):
        """
        :return: a list of expiry dates
        """
        return self.option_chains_by_expiry.keys()

    def get_option_chain_by_expiry(self, expiry):
        """
        :param expiry: string in the form of "YYYY-MM-DD"
        :return: return an option chain with the given expiry, or None if expiry is not valid
        """
        return self.option_chains_by_expiry.get(expiry, None)

    def get_option_by_symbol(self, symbol):
        """
        :param symbol: an option symbol (structure: "SPY:2021:07:02:CALL:425")
        :return: the option if present, or None if cannot be found
        """
        return self.symbol_to_option.get(symbol, None)