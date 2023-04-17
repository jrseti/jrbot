from abc import ABC, abstractmethod

class API(ABC):
    """Abstract class for trading APIs."""

    def __init__(self, api_name):

        self.api_name = api_name
       
    @abstractmethod
    def get_api_name(self):
        return self.api.name
    
    @abstractmethod
    def get_api_name(self):
        return self.api.name
    
    @abstractmethod
    def get_price(self, ticker, return_raw = False):
        """Get the current price of a ticker
        Args:
            ticker (str): The ticker to get the price of
            return_raw (bool): Whether to return the raw price object or not
        Returns:
            (bid_price, ask_price) (tuple): The bid and ask price of the ticker
        """
        pass

    @abstractmethod
    def get_balance(self, ticker):
        pass

    @abstractmethod
    def get_positions(self):
        pass

    @abstractmethod
    def place_order(self, ticker, quantity, order_type, order_side):
        pass

    @abstractmethod
    def cancel_order(self, order_id):
        pass

    def get_order(self, order_id):
        pass

    @abstractmethod
    def is_account_active(self):
        pass

    @abstractmethod
    def is_account_active(self):
        pass