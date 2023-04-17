import logging, logging.handlers
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL

class Logger():

    def __init__(self, config):
        self.config = config
        self.host = config["LOG_HOST"]
        self.port = config["LOG_PORT"]

    def get_logger(self, name):
        logger = logging.getLogger(name)
        if logger.hasHandlers() == False:
            logger.setLevel(logging.DEBUG)
            udp_handler = logging.handlers.DatagramHandler(self.host, self.port) 
            logger.addHandler(udp_handler)
        return logger

    def info(self, name, message):
        self.get_logger(name).log(INFO, message)

    def warn(self, name, message):
        self.get_logger(name).log(WARNING, message)

    def error(self, name, message):
        self.get_logger(name).log(ERROR, message)

    def debug(self, name, message):
        self.get_logger(name).log(DEBUG, message)

    def critical(self, name, message):      
        self.get_logger(name).log(CRITICAL, message)

if __name__ == "__main__":
    config = {
        "LOG_HOST" : "localhost",
        "LOG_PORT" : 19987
    }
    logger = Logger(config)
    logger.info("test_logger", 'This is a test message')
    logger.error("test_logger", 'This is a test message')
