import logging
from datetime import datetime

current_date_time = datetime.now().strftime("%Y%m%d_%H%M%S")


class Logger:
    @staticmethod
    def get_logger(module_name):

        logger = logging.getLogger(module_name)
        logger.setLevel(logging.DEBUG)

        if not logger.hasHandlers():
            handler = logging.FileHandler(f"log_{current_date_time}.log")
            handler.setLevel(logging.DEBUG)

            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                          datefmt='%d-%m-%y %H:%M:%S')
            handler.setFormatter(formatter)

            logger.addHandler(handler)

        return logger
