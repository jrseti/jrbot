import os

config = {
    # PROCESS MANAGEMENT
    "PID_FILE" : os.path.join(os.getcwd(), "pid.txt"),
    "PID_LOCK_FILE" : os.path.join(os.getcwd(), "pid.lock"),
    # LOGGING CONGURATION
    "LOG_DIRECTORY" : os.path.join(os.getcwd(), "logs"),
    "SERVER_LOG_FILE" : os.path.join(os.getcwd(), "logs", "log_server.log"),
    "LOG_HOST" : "localhost",
    "LOG_PORT" : 19987,
    "LOG_MESSAGE_FORMAT" : "%(created)f %(levelname)-8s %(message)s",
    "LOG_NAME" : "log_server",
    "LOG_SERVER_POLL_INTERVAL" : 0.1,
    "REDIS_STREAM_HOST" : "localhost",
    "REDIS_STREAM_PORT" : 6379,
    "REDIS_STREAM_DB" : 0,
    "REDIS_STREAM_STOCK_DATA_PRODUCER" : "stock_retriever",
    # REDIS
    "REDIS_HOST" : "localhost",
    "REDIS_PORT" : 6379,
}