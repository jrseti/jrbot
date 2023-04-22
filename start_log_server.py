import sys
from trading_logging import logger_server
from config import config
import utils

if __name__ == "__main__":
    utils.add_process_to_pid_list(sys.argv[0])
    logger_server.run_server(config)