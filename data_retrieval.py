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

def datetimeToFormattedString(dt):
    """Convert a timestamp to a formatted string with
    6 decimal places.
    Args:
        ts (float): The datetimeto convert
    Returns:
        str: The formatted string"""
    return f"{datetime.timestamp(dt):.6f}"

def send_message(redis_conn, logger, producer, message_channel, counter, data, keys_for_message):
    """Compose the message to send to the redis stream
    Args:
        redis_conn (redis.Redis): The redis connection
        logger (Logger): The logger
        producer (str): The producer of the message
        message_channel (str): The channel of the message
        counter (int): The counter of the message
        data (dict): The data to send
        keys_for_message (list): The keys to send
    """
    try:
        
        # The timestamp is a datetime object, convert it to a unix timestamp
        # string with 6 decimal places.
        data['timestamp'] = datetimeToFormattedString(data['timestamp'])

        # Compose the message and send to redis
        # The redis message does not have the type identifier like "T" or "B"
        message = ""
        keys_for_redis = keys_for_message.copy()
        keys_for_redis.remove('id_string')
        for key in keys_for_redis:
            message += str(data[key]) + ","
        message = message[:-1]
        send_data(redis_conn, producer, message_channel, message, counter)

        # Compose the message for logging and send to logger
        # The logger message does not have the ticker
        keys_for_log = keys_for_message.copy()
        keys_for_log.remove('ticker')
        message = ""
        for key in keys_for_log:
            message += str(data[key]) + ","
        message = message[:-1]
        logger.info(data['ticker'], message)

    except Exception as e:
        print(e)
    
    return
    
def send_data(redis_conn, producer, message_channel, message, counter):
    
    """Send data to redis stream
    Args:
        redis_conn (redis.Redis): The redis connection
        producer (str): The producer of the message
        message_channel (str): The channel of the message
        message (str): The message to send
        counter (int): The counter of the message"""
    try:
        data = {
            "producer": producer,
            "channel": message_channel,
            "message": message,
            "count": counter
        }
        redis_conn.xadd(producer, data)
        counter += 1
    except Exception as e:
        print(e)

    return


LOGGING_APP_NAME = "bot"
tickers = ['SPY', 'TSLA', 'GOOGL']
message_counter = 1

def run(logger, trading_api_name):
    """Run the trading bot"""

    global LOGGING_APP_NAME
    global tickers
    
    # initialize the logger (imported from logger)
    logger = Logger(config)

    logger.info(LOGGING_APP_NAME, f'Starting {trading_api_name} trading bot')
    logger.info(LOGGING_APP_NAME, 'Quote format: Q,utc timestamp,bid_price,ask_price,bid_size,ask_size')
    logger.info(LOGGING_APP_NAME, 'Trade format: T,utc timestamp,price,size')
    logger.info(LOGGING_APP_NAME, 'Bar format: B,utc timestamp,minutes_timespan,open,high,low,close,volume,vwap,trade_count')
    logger.info(LOGGING_APP_NAME, 'Updated Bar format: BU,utc timestamp,minutes_timespan,open,high,low,close,volume,vwap,trade_count')

    redis_conn = redis.Redis(host='localhost', port=6379, db=0)
    
    REDIS_PRODUCER = "data_retriever1"
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
    
    # async handlers
    def quote_data_handler(data):

        global message_counter
        data['id_string'] = "Q"
        keys = ['ticker', 'id_string', 'timestamp', 'bid_price', 'ask_price', 'bid_size', 'ask_size']
        send_message(redis_conn, logger, REDIS_PRODUCER, 'quotes', message_counter, data, keys)
        message_counter += 1
        return
    
    def trade_data_handler(data):

        global message_counter
        data['id_string'] = "T"
        keys = ['ticker', 'id_string', 'timestamp', 'price', 'size']
        send_message(redis_conn, logger, REDIS_PRODUCER, 'trades', message_counter, data, keys)
        message_counter += 1
        return
        
    def updated_bar_handler(data):

        global message_counter
        data['id_string'] = "BU"
        data['minute_span'] = "1"
        keys = ['ticker', 'id_string', 'timestamp', 'minute_span', 'open', 'high', 'low', 'close', 'volume', 'vwap', 'trade_count']
        send_message(redis_conn, logger, REDIS_PRODUCER, 'bars_updated', message_counter, data, keys)
        message_counter += 1
        return
    
    def bars_handler(data):

        global message_counter
        data['id_string'] = "B"
        data['minute_span'] = "1"
        keys = ['ticker', 'id_string', 'timestamp', 'minute_span', 'open', 'high', 'low', 'close', 'volume', 'vwap', 'trade_count']
        send_message(redis_conn, logger, REDIS_PRODUCER, 'bars', message_counter, data, keys)
        message_counter += 1
        return
        
    #api.start_data_stream(tickers, quote_data_handler, bars_handler, trade_data_handler, updated_bar_handler )
    api.start_data_stream(tickers, None, bars_handler, trade_data_handler, updated_bar_handler )
    

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
