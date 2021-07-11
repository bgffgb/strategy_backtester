class OptionChain:
    """
    A wrapper class to represent an option chain for a given point in time
    """
    def __init__(self, ticker, quotedate, option_list=None):
        """

        :param ticker: ticker string of the underlying ("SPY", "QQQ", ...)
        :param quotedate: date string (YYYY-MM-DD) when the quote was taken, as used in the DB
        :param option_list: a list of Option classes to initialize the chain (optional)
        """

        self.ticker = ticker
        self.quotedate = quotedate
        self.tot_options = 0
        self.options = []

        if option_list:
            for o in option_list:
                self.add_option(o)

    def add_option(self, o):
        self.tot_options += 1
        self.options.append(o)