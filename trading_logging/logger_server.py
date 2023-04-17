# -*- coding: UTF-8 -*-

import os
import time
from datetime import datetime
import logging, logging.handlers
from logging import LogRecord
from socketserver import BaseRequestHandler
from socketserver import UDPServer
import pickle
import codecs

# Create a class to handle logging over UDP
# A lot of effort went into rotating the log files and also
# creating a new directory for each day or time period.

log_server_config = {}

class MyTimedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """Class to handle log rotation. Based on TimedRotatingFileHandler and 
    modified to create a new directory for each rollover period"""

    def __init__(self, log_title, whenTo="midnight", intervals=1):
        """Constructor
        Arguments:
            log_title {str} -- log file name
            Keyword Arguments:
                whenTo {str} -- when to rotate the log file (default: {"midnight"})
                intervals {int} -- intervals to rotate the log file (default: {1})
        """
        global log_server_config

        self.when = whenTo.upper()
        self.inter = intervals
        self.log_file_path = os.path.abspath(log_server_config["LOG_DIRECTORY"])
        if not os.path.isdir(self.log_file_path):
            os.mkdir(self.log_file_path)
        if self.when == "S":
            self.extStyle = "%Y%m%d%H%M%S"
        if self.when == "M":
            self.extStyle = "%Y%m%d%H%M"
        if self.when == "H":
            self.extStyle = "%Y%m%d%H"
        if self.when == "MIDNIGHT" or self.when == "D":
            self.extStyle = "%Y%m%d"

        self.dir_log = os.path.abspath(os.path.join(self.log_file_path, datetime.now().strftime(self.extStyle)))
        if not os.path.isdir(self.dir_log):
            os.mkdir(self.dir_log)
        self.title = log_title
        filename = os.path.join(self.dir_log, self.title)
        logging.handlers.TimedRotatingFileHandler.__init__(self, filename, when=whenTo, interval=self.inter, backupCount=0)
        self._header = ""
        self._log = None
        self._counter = 0 
        self._last_rollover_time_item = -1


    def shouldRollover(self, record):
        """Determine if rollover should occur.
            Basically, see if the time of the record shoulf cause a rollover to occur.
            If it does, then call doRollover()
        Arguments:
            record {LogRecord} -- The record to be logged
        Returns:
            1 -- if rollover should occur
            0 -- if rollover should not occur
        """
        global log_server_config

        datetime_of_record = datetime.fromtimestamp(record.created)

        if self.when == "S":
            second_now = datetime_of_record.second
            if second_now != self._last_rollover_time_item:
                self._last_rollover_time_item = second_now
                #print("Forcing rollover")
                return 1
        if self.when == "M":
            minute_now = datetime_of_record.minute
            if minute_now != self._last_rollover_time_item:
                self._last_rollover_time_item = minute_now
                #print("Forcing rollover")
                return 1
        if self.when == "H":
            hour_now = datetime_of_record.hour
            if hour_now != self._last_rollover_time_item:
                self._last_rollover_time_item = hour_now
                #print("Forcing rollover")
                return 1
        if self.when == "MIDNIGHT" or self.when == "D":
            day_now = datetime_of_record.day
            if day_now != self._last_rollover_time_item:
                self._last_rollover_time_item = day_now
                #print("Forcing rollover")
                return 1

        return 0

    def doRollover(self):
        """Roll over the current log file to a new file."""
        print("LOG ROLLOVER")
        self.stream.close()
        # get the time that this sequence started at and make it a TimeTuple
        t = self.rolloverAt - self.interval
        timeTuple = time.localtime(t)

        self.new_dir = os.path.abspath(os.path.join(self.log_file_path, datetime.now().strftime(self.extStyle)))

        if not os.path.isdir(self.new_dir):
            os.mkdir(self.new_dir)
        self.baseFilename = os.path.abspath(os.path.join(self.new_dir, self.title))
        if self.encoding:
            self.stream = codecs.open(self.baseFilename, "a", self.encoding)
        else:
            self.stream = open(self.baseFilename, "a")

        self.rolloverAt = self.rolloverAt + self.interval

class UDPLogServerHandler(BaseRequestHandler):
    """Class to handle UDP log messages"""
    
    def handle(self):
        """Handle the UDP log message"""

        chunk = self.request[0]
        data = pickle.loads(chunk[4:])
        if len(data) == 0:
            return
        try:
            record = LogRecord(data['name'], data['levelno'], None, None, 
                               data['msg'], data['args'], data['exc_info'])
            self.handleLogRecord(record)
        except Exception as e:
            self.handleLogRecord(LogRecord("log_server", logging.ERROR, None, None, 
                                           "Error in UDPLogServerHandler.handle: {}".format(e),
                                             None, None))
    
    @staticmethod
    def handleLogRecord(record):
        """Handle the log record
        Arguments:
            record {LogRecord} -- The record to be logged
        """

        # If logger named from record.name does not exist, create it
        this_logger = logging.getLogger(record.name)
        #print("NAME: {}".format(record.name))
        if this_logger.hasHandlers() is False:
            #print("ADDED HANDLER TO LOGGER: {}".format(record.name))
            # Handler to roll log every day ay midnight
            timed_handler = MyTimedRotatingFileHandler(record.name + ".log", whenTo="MIDNIGHT", intervals=1)
            messageFormatter = logging.Formatter(log_server_config["LOG_MESSAGE_FORMAT"])
            timed_handler.setFormatter(messageFormatter)
            this_logger.addHandler(timed_handler)
            #print(this_logger)
        this_logger.handle(record)

def run_server(config):

    """ Run the UDP log server
    Arguments:
        config {dict} -- The configuration dictionary

    Note: Requires the following keys to have valis values in the config dictionary:
        "LOG_DIRECTORY", "SERVER_LOG_FILE",
        "LOG_HOST", "LOG_PORT", "LOG_MESSAGE_FORMAT",
        "LOG_NAME","LOG_SERVER_POLL_INTERVAL"
    """

    # Check for the required keys to be in the config dictionary.
    # Raise an exception if any are missing.
    required_config_keys = ["LOG_DIRECTORY", "SERVER_LOG_FILE",
                             "LOG_HOST", "LOG_PORT", "LOG_MESSAGE_FORMAT",
                             "LOG_NAME","LOG_SERVER_POLL_INTERVAL"]
    for key in required_config_keys:
        if key not in config:
            raise ValueError(f"Missing required key: {key}, check the config file.")

    # Store config in a global variable
    global log_server_config
    log_server_config = config

    try:
        # Get the root logger, define the message format and set the log level
        logger = logging.getLogger('')
        messageFormatter = logging.Formatter(log_server_config["LOG_MESSAGE_FORMAT"])
        logger.setLevel(logging.INFO)

        log_name = log_server_config["LOG_NAME"]
        host = log_server_config['LOG_HOST']
        port = log_server_config['LOG_PORT']

        # Create the UDP server to handle log messages
        server = UDPServer((host, port), UDPLogServerHandler)
        logger.info("Log Server Listening on %s:%s" % (host, port))
        message = f"Listening on {host} : {port}"
        print(message)
        UDPLogServerHandler.handleLogRecord(LogRecord(log_name, logging.INFO, 
                                                      None, None, message,
                                                      None, None))

        # Serve forever
        server.serve_forever(poll_interval=log_server_config["LOG_SERVER_POLL_INTERVAL"])
    except (IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        UDPLogServerHandler.handleLogRecord(LogRecord(log_name, logging.INFO, None, None, 
                                           f"Log server shut down with Ctrl+C",
                                             None, None))
        print ("Crtl+C Pressed. Shutting down.")




        