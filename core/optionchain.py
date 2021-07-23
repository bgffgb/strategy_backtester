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
        self.calls = []
        self.puts = []
        self.sorted = False

        if option_list:
            for o in option_list:
                self.add_option(o)

    def add_option(self, o):
        self.tot_options += 1
        self.options.append(o)
        self.sorted = False

        if o.type == 'CALL':
            self.calls.append((o.strike, o))
        if o.type == 'PUT':
            self.puts.append((o.strike, o))

    def make_sorted(self):
        self.calls.sort()
        self.puts.sort()
        self.sorted = True

    def get_sorted_calls(self):
        if not self.sorted:
            self.make_sorted()
        return self.calls

    def get_sorted_puts(self):
        if not self.sorted:
            self.make_sorted()
        return self.puts