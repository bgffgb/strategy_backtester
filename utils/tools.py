from datetime import date


def nr_days_between_dates(date1, date2):
    """
    :param date1: a date string in the form of "YYYY-MM-DD"
    :param date2: a date string in the form of "YYYY-MM-DD"
    :return: number of days between two dates
    """
    year1, month1, day1 = date1.split("-")
    year2, month2, day2 = date2.split("-")
    d1 = date(int(year1), int(month1), int(day1))
    d2 = date(int(year2), int(month2), int(day2))
    delta = d2 - d1
    return abs(delta.days)


def symbol_to_params(symbol):
    """
    Dirty function to turn symbol into option info
    If symbol formatting is not correct, returns symbol and 3x Nones
    :param symbol: str in the format of "SPY:2021:07:02:CALL:425"
    :return:
        ticker (ie: "SPY")
        expiry (str, "YYYY-MM-DD" format)
        option type ("CALL" or "PUT")
        strike (float)
    """
    arr = symbol.split(":")
    if len(arr) < 6:
        return symbol, None, None, None
    ticker = arr[0]
    expiry = arr[1] + "-" + arr[2] + "-" + arr[3]
    option_type = arr[4]
    strike = float(arr[5])
    return ticker, expiry, option_type, strike
