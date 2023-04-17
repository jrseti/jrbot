# encoding: utf-8
from trading_logging.logger import Logger
import sys
import signal
from datetime import datetime
from trading_api_config import config as api_config
from config import config as config
import redis

#from trading_apis.trading_api import TradingAPI
from trading_apis.alpaca_api import AlpacaAPI

LOGGING_APP_NAME = "bot"

# check our trading account
def check_account_ok(api, logger):
    try:
        if api.is_account_active() == False:
            logger.error(LOGGING_APP_NAME, 'The account is not ACTIVE, aborting')
            sys.exit()
    except Exception as e:
        logger.error(LOGGING_APP_NAME, 'Could not get account info, aborting')
        logger.error(LOGGING_APP_NAME, str(e))
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


# execute trading bot

def run(logger, trading_api_name):

# initialize the logger (imported from logger)
    logger = Logger(config)

    logger.info(LOGGING_APP_NAME, f'Starting {trading_api_name} trading bot')
    logger.info(LOGGING_APP_NAME, 'Quote format: Q,utc timestamp,bid_price,ask_price,bid_size,ask_size')
    logger.info(LOGGING_APP_NAME, 'Trade format: T,utc timestamp,price,size')
    logger.info(LOGGING_APP_NAME, 'Bar format: B,utc timestamp,open,high,low,close,volume,vwap,trade_count')
    logger.info(LOGGING_APP_NAME, 'Updated Bar format: BU,utc timestamp,open,high,low,close,volume,vwap,trade_count')

    redis_conn = redis.Redis(host='localhost', port=6379, db=0)
    if redis_conn is None:
        logger.error(LOGGING_APP_NAME, 'Could not connect to Redis, aborting')
        sys.exit()

    # initialize trading API
    api = None
    if trading_api_name.upper() == 'ALPACA':
        api = AlpacaAPI(api_config['ALPACA']) # initialize trading API

    if api is None:
        logger.error(LOGGING_APP_NAME, f'Could not initialize trading API {trading_api_name}, aborting')
        sys.exit()

    # check our trading account
    check_account_ok(api, logger)

    tickers = ['SPY', 'TSLA']

    # async handlers
    def quote_data_handler(data):
        # quote data will arrive here
        dt = datetime.timestamp(data['timestamp'])
        message =f"Q,{dt:.6f},{data['bid_price']},{data['ask_price']},{data['bid_size']},{data['ask_size']}"
        logger.info(data['ticker'], message)

        message =f"{data['ticker']},{dt:.6f},{data['bid_price']},{data['ask_price']},{data['bid_size']},{data['ask_size']}"
        redis_conn.publish('quotes', message)

    def trade_data_handler(data):
        # trade data will arrive here
        dt = datetime.timestamp(data['timestamp'])
        message =f"T,{dt:.6f},{data['price']},{data['size']}"
        logger.info(data['ticker'], message)

        message =f"{data['ticker']},{dt:.6f},{data['price']},{data['size']}"
        redis_conn.publish('trades', message)

    def updated_bar_handler(data):
        # updated bar data will arrive here
        dt = datetime.timestamp(data['timestamp'])
        message =f"BU,{dt:.6f},{data['open']},{data['high']},{data['low']},{data['close']},{data['volume'],data['vwap'],data['trade_count']}"
        logger.info(data['ticker'], message)

        message = f"{data['ticker']},{dt:.6f},{data['open']},{data['high']},{data['low']},{data['close']},{data['volume'],data['vwap'],data['trade_count']}"
        message = message.replace("(", "").replace(")", "").replace(" ", "")
        redis_conn.publish('bars_updated', message)
        

    def bars_handler(data):
        # One minute bar data will arrive here
        dt = datetime.timestamp(data['timestamp'])
        message =f"B,{dt:.6f},{data['open']},{data['high']},{data['low']},{data['close']},{data['volume'],data['vwap'],data['trade_count']}"
        logger.info(data['ticker'], message)

        message = f"{data['ticker']},{dt:.6f},{data['open']},{data['high']},{data['low']},{data['close']},{data['volume'],data['vwap'],data['trade_count']}"
        message = message.replace("(", "").replace(")", "").replace(" ", "")
        redis_conn.publish('bars', message)

    api.start_data_stream(tickers, quote_data_handler, bars_handler, trade_data_handler, updated_bar_handler )
    

# execute trading bot
def main():

    global LOGGING_APP_NAME
    try:
        trading_api_name = str(sys.argv[1])
        LOGGING_APP_NAME += f"_{trading_api_name}"
        logger = Logger(config)
        run(logger, trading_api_name)
    except (IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        logger.info(LOGGING_APP_NAME, f"Log server shut down with Ctrl+C")
        print ("Crtl+C Pressed. Shutting down.")

if __name__ == '__main__':
    main()
