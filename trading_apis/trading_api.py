from api import API


class TradingAPI(API):

    def __init__(self, api_name):

        self.api = None

        if api_name == 'alpaca':
            from alpaca_api import AlpacaAPI
            self.api = AlpacaAPI()

    def get_api(self):
        return self.api
    
    def get_api_name(self):
        return self.api.name
    
    def get_api_name(self):
        return self.api.name
    
    def get_price(self, ticker):
        return self.api.get_price(ticker)

    def get_balance(self, ticker):
        pass

    def get_positions(self):
        pass

    def place_order(self, ticker, quantity, order_type, order_side):
        pass

    def cancel_order(self, order_id):
        pass

    def get_order(self, order_id):
        pass

    def is_account_active(self):
        return self.api.is_account_active()
    
    def start_data_stream(self, tickers, quote_handler, minute_bars_handler, trades_handler, updated_bars_handler):
        pass

    def stop_quote_stream(self):
        pass

if __name__ == '__main__':
    
    api = TradingAPI("alpaca")
    print(api.get_price('TSLA'))
