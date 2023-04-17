import os

config = {
    # LOGGING CONGURATION
    "LOG_DIRECTORY" : os.path.join(os.getcwd(), "logs"),
    "SERVER_LOG_FILE" : os.path.join(os.getcwd(), "logs", "log_server.log"),
    "LOG_HOST" : "localhost",
    "LOG_PORT" : 19987,
    "LOG_MESSAGE_FORMAT" : "%(created)f %(levelname)-8s %(message)s",
    "LOG_NAME" : "log_server",
    "LOG_SERVER_POLL_INTERVAL" : 0.1
}