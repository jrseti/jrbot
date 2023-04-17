from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.data.requests import StockLatestBarRequest
from alpaca.data.requests import StockBarsRequest

from alpaca.trading.client import TradingClient
from alpaca.data.live import StockDataStream

from alpaca.data.timeframe import TimeFrame
from datetime import datetime

from .api import API

class AlpacaAPI(API):
    def __init__(self, config):
        super().__init__("alpaca")
        self.config = config

        self.client = StockHistoricalDataClient(config["API_KEY"],  config["API_SECRET_KEY"])
        self.trade_client = TradingClient(config["API_KEY"],  config["API_SECRET_KEY"], paper=config["IS_PAPER"])
        self.stock_data_stream = None
        self.balance = 1000
        self.positions = []
        self.orders = []
        self.order_id = 0

        self.quote_handler = None
        self.trades_handler = None
        self.bars_handler = None
        self.updated_bar_handler = None

    def get_api_name(self):
        return self.api.name

    def get_price(self, ticker, return_raw = False):
        """Get the current price of a ticker
        Args:
            ticker (str): The ticker to get the price of
            return_raw (bool): Whether to return the raw price object or not
        Returns:
            (bid_price, ask_price) (tuple): The bid and ask price of the ticker
        """
        #request = StockLatestBarRequest(symbol_or_symbols=ticker, bar_size='1Min', bar_type='trades')
        #bar = self.client.get_stock_latest_bar(request)[ticker]
        price =  self.client.get_stock_latest_quote(StockLatestQuoteRequest(symbol_or_symbols=ticker))

        if return_raw is True:
            return price
        return price.bid_price, price.ask_price

    def get_balance(self, ticker):
        return self.balance

    def get_positions(self):
        return self.positions

    def place_order(self, ticker, quantity, order_type, order_side):
        self.order_id += 1
        self.orders.append(self.order_id)
        return self.order_id

    def cancel_order(self, order_id):
        self.orders.remove(order_id)

    def get_order(self, order_id):
        return order_id in self.orders

    def is_account_active(self):
        account = self.trade_client.get_account()
        print(account)
        status = account.status
        if account.status == "ACTIVE":
            return True
        return False
    
    def is_ticker_tradable(self, ticker):
        pass

    def get_quote(self, ticker):
        self.client

    def start_data_stream(self, tickers, quote_handler, minute_bars_handler, trades_handler, updated_bars_handler):

        # Attempt to stop the quote stream if it exists
        try:
            if self.stock_data_stream is not None:
                self.stock_data_stream.stop()
                self.stock_data_stream.close()
                self.stock_data_stream = None

                self.quote_handler = None
                self.trades_handler = None
        except Exception as e:
            print(f"Failed to stop quote stream: {e}")
            pass

        # Create the quote stream if it does not exist
        try: 
            if self.stock_data_stream is None:
                self.stock_data_stream = StockDataStream(self.config["API_KEY"], self.config["API_SECRET_KEY"])
        except Exception as e:
            print(f"Failed to create quote stream: {e}")
            return False     
                            
        # Subscribe to the stream with handlers
        # TODO: Add support for minute bars, trades, and updated bars
        try:
            if self.quote_handler is not None:
                self.stock_data_stream.unsubscribe_quotes(tickers)
            self.quote_handler = quote_handler
            self.stock_data_stream.subscribe_quotes(self._quote_handler, *tickers)

            if self.trades_handler is not None:
                self.stock_data_stream.unsubscribe_trades(tickers)
            self.trades_handler = trades_handler
            self.stock_data_stream.subscribe_trades(self._trades_handler, *tickers)

            if self.updated_bar_handler is not None:
                self.stock_data_stream.unsubscribe_updated_bars(tickers)
            self.updated_bar_handler = updated_bars_handler
            self.stock_data_stream.subscribe_updated_bars(self._updated_bars_handler, *tickers)

            if self.bars_handler is not None:
                self.stock_data_stream.unsubscribe_bars(tickers)
            self.bars_handler = minute_bars_handler 
            self.stock_data_stream.subscribe_bars(self._bars_handler, *tickers)
            
        except Exception as e:
            print(f"Failed to subscribe to quote stream: {e}")
            return False
        
        # Start the run loop
        self.stock_data_stream.run()
        
        # Yay! We made it this far. Return True
        return True
    
    def stop_quote_stream(self):

        # Attempt to stop the quote stream if it exists
        try:
            if self.stock_data_stream is not None:
                self.stock_data_stream.close()
                self.stock_data_stream.stop_ws()
                self.stock_data_stream = None
                print("Alpaca stock streams stopped")
        except:
            return False
        
        return True
    
    def close(self):
        self.stop_quote_stream()
        if self.stock_data_stream != None:
            self.stock_data_stream.stop()

    async def _quote_handler(self, quote):
        """Quote handler for the Alpaca API. 
        Converts the quote object to a dictionary and passes it to the quote handler.
        Args:
            quote (Quote): The quote object
        """
        if self.quote_handler != None:
            #print(quote)
            quote_dict = {"ticker": quote.symbol, 
                          "bid_price": quote.bid_price, 
                          "ask_price": quote.ask_price, 
                          "timestamp": quote.timestamp,
                          "bid_size": quote.bid_size,
                          "ask_size": quote.ask_size}
            self.quote_handler(quote_dict)
 
    async def _trades_handler(self, trade):
        if self.trades_handler != None:
            #print(trade)
            trades_dict = {"ticker": trade.symbol, "price": trade.price, "size": trade.size, "timestamp": trade.timestamp}
            self.trades_handler(trades_dict)
            #print(trade)

    async def _updated_bars_handler(self, bar):
        if self.updated_bar_handler != None:
            bar_dict = {"ticker": bar.symbol, "open": bar.open,
                        "high": bar.high, "low": bar.low, 
                        "close": bar.close, 
                        "volume": bar.volume, 
                        "trade_count": bar.trade_count,
                        "vwap": bar.vwap,
                        "timestamp": bar.timestamp}
            self.updated_bar_handler(bar_dict)
        #print(bar)

    async def _bars_handler(self, bar):
        if self.bars_handler != None:
            bar_dict = {"ticker": bar.symbol, "open": bar.open,
                         "high": bar.high, "low": bar.low, 
                         "close": bar.close, 
                         "volume": bar.volume, 
                         "trade_count": bar.trade_count,
                         "vwap": bar.vwap,
                         "timestamp": bar.timestamp}
            self.bars_handler(bar_dict)
            #
        #print(bar)

        

        
    
if __name__ == '__main__':
    api = AlpacaAPI()
    print(api.get_price("TSLA"))
    print(f"Is account active: {api.is_account_active()}")

