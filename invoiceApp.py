import yaml

from ExcelParser import ExcelParser
from GreenInvoiceHandler import GreenInvoiceHandler
from logger import Logger


class InvoiceApp:
    def __init__(self):
        self.logger = Logger.get_logger("main")
        self.logger.info("Starting Invoice App...")

        self.key, self.secret = self.read_cred()
        self.green_invoice_client = GreenInvoiceHandler(self.key, self.secret)
        self.green_invoice_client.generate_token()

        self.file = ExcelParser("Samples/August.xlsx")

        self.client = None
        self.date_paid = None
        self.amount_paid = None
        self.number_of_treatments = None
        self.treatments = None
        self.payment_method = None
        self.bank_details = None
        self.invoice = None
        self.notes = None

        self.run()

        # self.green_invoice_client.search_client_by_name('Jenna Reichman')

    def read_cred(self, file_path="Samples/Credentials.yml"):
        try:
            with open(file_path, 'r') as f:
                creds = yaml.safe_load(f)

            key = creds.get('key')
            secret = creds.get('secret')

            return key, secret
        except FileNotFoundError as fileNotFoundErr:
            self.logger.error(f"error in opening file: {fileNotFoundErr}")
            exit(-1)
        except:
            self.logger.error(f"Unexpected error in opening file: {file_path}")
            exit(-1)

    def run(self):
        for row_index, row_data in enumerate(self.file.data):
            self.logger.debug(f"Starting row {row_index}")
            self.__parse_data(row_index)
            if self.invoice:
                self.logger.critical(f"{self.client} already has an invoice")
                exit(-2)

            print(f"Row {row_index}: {row_data}")

    def __parse_data(self, row_index):
        try:
            row_data = self.file.get_row(row_index)
        except Exception as e:
            self.logger.error(f"Error in parsing data: {e}")
            exit(-1)
        try:
            self.client = self.file.get_cell(row_data, 'Client')
            self.date_paid = self.file.get_cell(row_data, 'Date Paid')
            self.amount_paid = self.file.get_cell(row_data, 'Amount Paid')
            self.number_of_treatments = self.file.get_cell(row_data, 'Number of Apts')
            self.treatments = self.file.get_cell(row_data, 'Treatment')
            self.payment_method = [self.file.get_cell(row_data, 'Paybox'), self.file.get_cell(row_data, 'Paybox')]
            self.bank_details = [self.file.get_cell(row_data, 'Bank'), self.file.get_cell(row_data, 'Bank Branch '),
                                 self.file.get_cell(row_data, 'Account #')]
            self.invoice = self.file.get_cell(row_data, 'Invoice')
            self.notes = self.file.get_cell(row_data, 'Notes')
        except Exception as e:
            self.logger.error(f"Error in parsing data: {e}")
            exit(-1)


        self.client = row_data['Client']
        self.date_paid = row_data['Date Paid']
        self.amount_paid = row_data['Amount Paid']


if __name__ == "__main__":
    app = InvoiceApp()
