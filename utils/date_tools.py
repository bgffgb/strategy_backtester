from datetime import date

def  nr_days_between_dates(date1, date2):
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
