import os
from datetime import datetime
import redis
from filelock import FileLock
import config
from trading_logging.logger import Logger
from trading_logging.logger_server import ping
import processes

"""This module contains utility functions for the trading bot."""

_redis_conn = None
_logger = None



def datetimeToFormattedString6(dt):
    """Convert a timestamp to a formatted string with
    6 decimal places.
    Args:
        ts (float): The datetimeto convert
    Returns:
        str: The formatted string"""
    return f"{datetime.timestamp(dt):.6f}"

def get_logger():
    """Get the logger.
    Returns:
        Logger: The logger instance. Creates it if it does not exist.
    """
    global _logger
    if _logger is not None:
        return _logger
    _logger = Logger(config.config)

    if ping(config.config) == False:
        raise Exception("Logger server is not running")
    return _logger

def get_redis():
    """Get a connection to the redis server.
    Returns:
        redis.Redis: The connection to the redis server"""
    global _redis_conn
    if _redis_conn is not None:
        return _redis_conn
    _redis_conn = redis.Redis(host=config.config['REDIS_HOST'], port=config.config['REDIS_PORT'], db=0)
    return _redis_conn

def add_process_to_pid_list(process_name):
    """Add the current process to the pid file.
    Args:
        process_name (str): The name of the process to add
    """
    processes.add_this_process_to_pid_list(os.path.basename(process_name))

def remove_process_from_list(process_name):
    """Remove the current process from the pid file.
    Args:
        process_name (str): The name of the process to remove
    """
    processes.remove_process_from_list(os.path.basename(process_name)) 


def send_stock_info_to_redis_stream(producer, message_channel, message, counter):
    
    """Send data to redis stream
    Args:
        producer (str): The producer of the message
        message_channel (str): The channel of the message
        message (str): The message to send
        counter (int): The counter of the message. This is used to ensure that the
            messages are in the correct order and none are missing"""
    try:
        data = {
            "producer": producer,
            "channel": message_channel,
            "message": message,
            "count": counter
        }
        get_redis().xadd(producer, data)
        counter += 1
    except Exception as e:
        print(e)

    return

def broadcast_stock_data(producer, message_channel, counter, data, keys_for_message):
    """Compose the message to send to the redis stream and the logger
    Args:
        producer (str): The producer of the message
        message_channel (str): The channel of the message
        counter (int): The counter of the message
        data (dict): The data to send
        keys_for_message (list): The keys to send
    """
    try:
        
        # The timestamp is a datetime object, convert it to a unix timestamp
        # string with 6 decimal places.
        data['timestamp'] = datetimeToFormattedString6(data['timestamp'])

        # Compose the message and send to redis
        # The redis message does not have the type identifier like "T" or "B"
        message = ""
        keys_for_redis = keys_for_message.copy()
        keys_for_redis.remove('id_string')
        for key in keys_for_redis:
            message += str(data[key]) + ","
        message = message[:-1]
        send_stock_info_to_redis_stream(producer, message_channel, message, counter)

        # Compose the message for logging and send to logger
        # The logger message does not have the ticker
        keys_for_log = keys_for_message.copy()
        keys_for_log.remove('ticker')
        message = ""
        for key in keys_for_log:
            message += str(data[key]) + ","
        message = message[:-1]
        get_logger().info(data['ticker'], message)

    except Exception as e:
        print(e)
    
    return
