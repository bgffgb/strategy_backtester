"""
Utility functions to handle getting data out of the DB in a structured way
"""
import logging
import records
import time

from core.option import Option
from core.optionchainset import OptionChainSet
from core.event import Event

logger = logging.getLogger(__name__)

# DB instance initialization
with open("credentials.txt") as f:
    username, password = f.readlines()
    username = username.strip()
    password = password.strip()
recdb = records.Database('mysql://'+username+':'+password+'@localhost/rtoptionsdb')


def events_generator(ticker, fromdate="2021-06-01", todate=None):
    """
    Loads in option data from the Database and yield Events in a a chronological order.
    Yield is used (instead of return) to reduce memory requirements & speed things up a bit.

    If no todate is provided, everything is queried from starting point

    :param ticker: string of the ticker ("SPY", "QQQ", ...)
    :param fromdate: date string (YYYY-MM-DD) from when events should be read form the DB (fromdate included)
    :param todate: date string (YYYY-MM-DD) until when events should be read form the DB (todate NOT included)
    :return: yields an Event as long as there are Events left
    """

    # Build up the query gradually
    query_str = "SELECT * FROM bt_OptionDataTable WHERE Ticker='" + ticker + "'"

    # TODO: Validate if fromdate, fromtime, todate, totime have correct syntax (YYYY-MM-DD and YYYY-MM-DDThh:mm:ss)
    if fromdate:
        query_str += " AND QuoteDate >= '" + fromdate + "'"
    else:
        logger.error("No fromdate is specified.")
        return

    if todate:
        query_str += " AND QuoteDate < '" + todate + "'"

    # Sort chronologically
    query_str += " ORDER BY QuoteDate;"
    logger.info("Running query: {}".format(query_str))

    # Run query - this can take a while
    tic = time.time()
    rows = recdb.query(query_str)
    toc = time.time()
    logger.info("Query took {} seconds".format(toc - tic))
    data = rows.export('df')
    logger.info("Processing {} total returned option records".format(len(data)))

    """
    Create events out of the options table rows.
    Option rows are sorted by UNIX timestamp in chronological order
    Group all option entries with the same QuoteDate into one big option chain
    containing everything/providing fast structured access.   
    """
    prevdate = None
    prevprice = None
    current_chains = None
    for j in range(len(data)):
        # Turn DB entry into an Option class instance
        o = Option(ticker=data.Ticker[j], expiry=data.OptExpDate[j], symbol=data.OptionSymbol[j],
                   strike=data.OptStrike[j], type=data.OptType[j], bid=data.OptBid[j], ask=data.OptAsk[j],
                   oi=data.OptOpenInterest[j], vol=data.OptVolume[j], quotedate=data.QuoteDate[j],
                   underlying=data.StockPrice[j], daytoexp=data.DaysToExp[j], iv=data.GreekIV[j],
                   delta=data.GreekDelta[j], gamma=data.GreekGamma[j], theta=data.GreekTheta[j], vega=data.GreekVega[j])

        if prevdate != o.quotedate:
            if prevdate:
                # Create new event based on data gathered so far
                # NOTE: deriving the price of the underlying from the option is a bit iffy;
                new_event = Event(ticker=ticker, price=prevprice, quotedate=prevdate, option_chains=current_chains)
                yield new_event

            prevdate = o.quotedate
            prevprice = o.underlying
            current_chains = OptionChainSet(ticker)
        else:
            # Add option to current option chain
            current_chains.add_option(o)

    # Last event
    new_event = Event(ticker=ticker, price=prevprice, quotedate=prevdate, option_chains=current_chains)
    yield new_event