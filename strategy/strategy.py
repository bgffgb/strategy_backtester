from abc import ABC, abstractmethod

from core.event import  Event


class Strategy:
    """
    Abstract interface class for all strategies to implement

      __init___: initialization is done with a dictionary of strategy specific parameters
      handle_event: gets a a new Event (with quotedate later than any previous event) and returns stock/option buy/sell
                    orders
    """

    def __init__(self):
        """
        :param params: a json of strategy specific parameters, mapping strings to their values
        """
        self.unique_id = ""

    @abstractmethod
    def handle_event(self, event: Event):
        """
        :param event: a new event with option chain data to react to
        :return: a list of Order classes
        """
        pass

    @abstractmethod
    def get_unique_id(self):
        """
        :return: the unique id string for this strategy
        """
        return self.unique_id

    @abstractmethod
    def set_unique_id(self, uid):
        """
        :param uid: a string to uniquely identify a strategy; handy when backtesting different combinations of parameters
        """
        self.unique_id = uid