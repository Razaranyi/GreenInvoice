from GreenInvoiceHandler import GreenInvoiceHandler
from logger import Logger


def main():
    logger = Logger.get_logger("main")
    logger.info("Start running")
    green_invoice_client = GreenInvoiceHandler('8d72431d-1a97-446f-99be-eb9feb27f03e', '0wpqN_ols4cn8Rv7lAIhJA')
    green_invoice_client.generate_token()
    green_invoice_client.search_client_by_name('Jenna Reichman')


if __name__ == '__main__':
    main()
