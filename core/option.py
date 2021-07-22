class Option:
    """
    A wrapper class to represent a single option
    """

    def __init__(self, ticker, expiry, symbol, strike, type, bid, ask, oi, vol, quotedate,
                 underlying=None, daytoexp=None, iv=None, delta=None, gamma=None, theta=None, vega=None):
        """
        :param ticker: ticker string of the underlying ("SPY", "QQQ", ...)
        :param symbol: uniqye string to identify an option contract (structure: SPY:2021:07:02:CALL:425)
        :param expiry: date string (YYYY-MM-DD) of option expiry
        :param strike: float of the strike price
        :param type: "PUT" or "CALL" (str)
        :param bid: bid price (float)
        :param ask: ask price (float)
        :param oi: open interest (int)
        :param vol: volume (int)
        :param quotedate: date string (YYYY-MM-DD) when the quote was taken, as used in the DB
        :param underlying: price of the underlying (float)
        :param daytoexp: days to expiry (int)
        :param iv: implied volatility (float)
        :param delta: greeks delta (float)
        :param gamma: greeks gamma (float)
        :param theta: greeks theta (float)
        :param vega: greeks vega (float)
        """
        self.ticker = ticker
        self.expiry = expiry
        self.symbol = symbol
        self.strike = strike
        self.type = type
        self.bid = bid
        self.ask = ask
        self.oi = oi
        self.vol = vol
        self.quotedate = quotedate
        self.underlying = underlying
        self.daytoexp = daytoexp
        self.iv = iv
        self.delta = delta
        self.gamma = gamma
        self.theta = theta
        self.vega = vega

    def __str__(self):
        return "{} quote time: {}".format(self.symbol, self.quotedate)

    def midprice(self):
        return 100 * (self.bid + self.ask) / 2