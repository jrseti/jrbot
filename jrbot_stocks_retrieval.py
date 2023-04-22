# encoding: utf-8
#from trading_logging.logger import Logger
import sys
import signal
from datetime import datetime
from trading_api_config import config as api_config
import config
import utils
import redis

#from trading_apis.trading_api import TradingAPI
from trading_apis.alpaca_api import AlpacaAPI

def logger():
    """Get the logger. This is a convenience function to avoid having to
    always type utils.get_logger()."""
    return utils.get_logger()

# check our trading account
def check_account_ok(api):
    try:
        if api.is_account_active() == False:
            logger().error(LOGGING_APP_NAME, 'The account is not ACTIVE, aborting')
            sys.exit()
    except Exception as e:
        logger().error(LOGGING_APP_NAME, 'Could not get account info, aborting')
        logger().error(LOGGING_APP_NAME, str(e))
        sys.exit()

# close current orders
"""def clean_open_orders(api):

    lg.info('Cancelling all orders...')

    try:
        api.cancel_all_orders()
        lg.info('All orders cancelled')
    except Exception as e:
        lg.error('Could not cancel all orders')
        lg.error(e)
        sys.exit()

def check_asset_ok(api,ticker):
    # check whether the asset is OK for trading
        # IN: ticker
        # OUT: True if it exists and is tradable / False otherwise
    try:
        asset = api.get_asset(ticker)
        if asset.tradable:
            lg.info('Asset exists and tradable')
            return True
        else:
            lg.info('Asset exists but not tradable, exiting')
            sys.exit()
    except Exception as e:
        lg.error('Asset does not exist or something happens!')
        lg.error(e)
        sys.exit()"""

LOGGING_APP_NAME = "bot"
tickers = ['SPY', 'TSLA', 'GOOGL']
message_counter = 1

def run(trading_api_name):
    """Run the trading bot"""

    global LOGGING_APP_NAME
    global tickers

    logger().info(LOGGING_APP_NAME, f'Starting {trading_api_name} trading bot')
    logger().info(LOGGING_APP_NAME, 'Quote format: Q,utc timestamp,bid_price,ask_price,bid_size,ask_size')
    logger().info(LOGGING_APP_NAME, 'Trade format: T,utc timestamp,price,size')
    logger().info(LOGGING_APP_NAME, 'Bar format: B,utc timestamp,minutes_timespan,open,high,low,close,volume,vwap,trade_count')
    logger().info(LOGGING_APP_NAME, 'Updated Bar format: BU,utc timestamp,minutes_timespan,open,high,low,close,volume,vwap,trade_count')
    
    REDIS_PRODUCER = "data_retriever1"
    if utils.get_redis() is None:
        logger().error(LOGGING_APP_NAME, 'Could not connect to Redis, aborting')
        sys.exit()

    # initialize trading API
    api = None
    if trading_api_name.upper() == 'ALPACA':
        api = AlpacaAPI(api_config['ALPACA']) # initialize trading API

    if api is None:
        logger().error(LOGGING_APP_NAME, f'Could not initialize trading API {trading_api_name}, aborting')
        sys.exit()

    # check our trading account
    check_account_ok(api)
    
    # async handlers
    def quote_data_handler(data):

        global message_counter
        data['id_string'] = "Q"
        keys = ['ticker', 'id_string', 'timestamp', 'bid_price', 'ask_price', 'bid_size', 'ask_size']
        utils.broadcast_stock_data(REDIS_PRODUCER, 'quotes', message_counter, data, keys)
        message_counter += 1
        return
    
    def trade_data_handler(data):

        global message_counter
        data['id_string'] = "T"
        keys = ['ticker', 'id_string', 'timestamp', 'price', 'size']
        utils.broadcast_stock_data(REDIS_PRODUCER, 'trades', message_counter, data, keys)
        message_counter += 1
        return
        
    def updated_bar_handler(data):

        global message_counter
        data['id_string'] = "BU"
        data['minute_span'] = "1"
        keys = ['ticker', 'id_string', 'timestamp', 'minute_span', 'open', 'high', 'low', 'close', 'volume', 'vwap', 'trade_count']
        utils.broadcast_stock_data(REDIS_PRODUCER, 'bars_updated', message_counter, data, keys)
        message_counter += 1
        return
    
    def bars_handler(data):

        global message_counter
        data['id_string'] = "B"
        data['minute_span'] = "1"
        keys = ['ticker', 'id_string', 'timestamp', 'minute_span', 'open', 'high', 'low', 'close', 'volume', 'vwap', 'trade_count']
        utils.broadcast_stock_data(REDIS_PRODUCER, 'bars', message_counter, data, keys)
        message_counter += 1
        return
        
    #api.start_data_stream(tickers, quote_data_handler, bars_handler, trade_data_handler, updated_bar_handler )
    api.start_data_stream(tickers, None, bars_handler, trade_data_handler, updated_bar_handler )
    

# execute trading bot
def main():

    global LOGGING_APP_NAME
    try:
        #trading_api_name = str(sys.argv[1])
        trading_api_name = "alpaca"
        LOGGING_APP_NAME += f"_{trading_api_name}"
        utils.add_process_to_pid_list(sys.argv[0])
        run(trading_api_name)
    except (IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        logger().info(LOGGING_APP_NAME, f"Log server shut down with Ctrl+C")
        print ("Crtl+C Pressed. Shutting down.")
        utils.remove_process_from_list(sys.argv[0])

if __name__ == '__main__':
    main()
