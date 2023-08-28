import json
import urllib.parse
from urllib.request import Request, urlopen
import os, os.path
import pathlib
from GreenInvoiceHandler import GreenInvoiceHandler
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG,
                    filename="logs.log",
                    filemode="w",
                    datefmt='%d-%m-%y %H:%M:%S')


def main():
    logger.info("Start running")
    green_invoice_client = GreenInvoiceHandler('8d72431d-1a97-446f-99be-eb9feb27f03e', '0wpqN_ols4cn8Rv7lAIhJA')
    green_invoice_client.generate_token()
    green_invoice_client.search_client_by_name('Jenna Reichman')


if __name__ == '__main__':
    main()
