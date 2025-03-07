import logging
import os
from datetime import datetime

class Logger:
    @staticmethod
    def get_logger(module_name):
        current_date_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        logger = logging.getLogger(module_name)
        logger.setLevel(logging.DEBUG)

        if not logger.hasHandlers():
            # Setting up a generic location - user's home directory
            log_directory = os.path.join(os.path.expanduser('~'), 'GreenInvoiceHandler_', 'Logs')
            os.makedirs(log_directory, exist_ok=True)  # Create the log directory if it doesn't exist

            # Log file path
            log_file_path = os.path.join(log_directory, f"log_{current_date_time}.log")

            # Creating the FileHandler
            handler = logging.FileHandler(log_file_path)
            handler.setLevel(logging.DEBUG)

            # Setting the format for the log messages
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                          datefmt='%d-%m-%y %H:%M:%S')
            handler.setFormatter(formatter)

            # Adding the handler to the logger
            logger.addHandler(handler)

        return logger
