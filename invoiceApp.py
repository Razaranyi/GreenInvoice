import yaml
import argparse
from datetime import datetime
from green_invoice.models import Currency, PaymentType

from ExcelParser import ExcelParser
from GreenInvoiceHandler import GreenInvoiceHandler
from logger import Logger


def get_cli_args():
    parser = argparse.ArgumentParser(description='Invoice App CLI')
    parser.add_argument('command', choices=['preview', 'generate'], help='Command to execute')
    parser.add_argument('--file', default=None, help='Path to the input file')
    args = parser.parse_args()
    return args


class InvoiceApp:

    def __init__(self, command, file_path=None):
        self.logger = Logger.get_logger("main")
        self.logger.info("Starting Invoice App...")

        self.command = command

        self.key, self.secret = self.__read_cred()
        self.green_invoice_client = GreenInvoiceHandler(self.key, self.secret)
        self.green_invoice_client.generate_token()

        if file_path:
            self.file = ExcelParser(file_path)
        else:
            file_path = input("Please enter the path to the input file: ")
            self.file = ExcelParser(file_path)

        self.allow_skips = True

        self.client = None
        self.date_paid = None
        self.amount_paid = None
        self.number_of_treatments = None
        self.treatments = None
        self.payment_method = None
        self.invoice = None
        self.bank_details = None
        self.app_number = None

        self.run()

    def run(self):
        for row_index, row_data in enumerate(self.file.data):
            self.logger.debug(f"Starting row {row_index}")
            self.__initialize_variables(row_index)
            self.logger.debug(f"Parsed {self.client} row")

            if self.invoice:
                if self.allow_skips:
                    self.logger.debug(f"Skipping invoice {self.invoice}")
                    continue
                else:
                    self.logger.critical(f"Invoice {self.invoice} already issued. Exit script")
                    exit(-1)

            client_id = self.green_invoice_client.search_client_by_name(self.client)
            if client_id is None:
                self.logger.warning(f"Client {self.client} not found")
                exit(-1)

            else:
                income_list = self.__construct_income_list()
                payment_details = self.__construct_payment_details()
                values = self.green_invoice_client.parse_values(client_id, payment_details, self.date_paid, income_list)
                if self.command == 'preview':
                    self.green_invoice_client.generate_new_invoice_preview(values, self.client)
                elif self.command == 'generate':
                    self.__handle_generate(row_index, values)
                else:
                    self.logger.error(f"Unknown command: {self.command}")
                    print(f"Unknown command: {self.command}. Exiting...")
                    exit(-1)

        self.logger.info("Finished processing all rows")

    def __handle_generate(self, row_index, values):
        self.green_invoice_client.generate_new_invoice(values, self.client)
        self.file.change_invoice_status(row_index)
        if self.allow_skips:
            self.allow_skips = False
            self.logger.debug(f"Allowing skips: {self.allow_skips}")

    def __initialize_variables(self, row_index):
        try:
            row_data = self.file.get_row(row_index)
        except Exception as e:
            self.logger.error(f"Error in parsing data: {e}")
            exit(-1)
        try:
            self.client = self.file.get_cell(row_data, 'Client')
            self.date_paid = self.__convert_date_paid(self.file.get_cell(row_data, 'Date Paid'))
            self.amount_paid = self.file.get_cell(row_data, 'Amount Paid')
            self.number_of_treatments = self.file.get_cell(row_data, 'Number of Apts')
            self.treatments = self.__convert_treatments_date(self.file.get_cell(row_data, 'Treatment'))
            self.bank_details = [self.file.get_cell(row_data, 'Bank'), self.file.get_cell(row_data, 'Bank Branch '),
                                 self.file.get_cell(row_data, 'Account #')]
            self.invoice = self.file.get_cell(row_data, 'Invoice')
            bit = self.file.get_cell(row_data, 'Bit')
            paybox = self.file.get_cell(row_data, 'Paybox')
            eft = self.file.get_cell(row_data, 'EFT')
            self.__get_payment_method(bit, paybox, eft)
        except Exception as e:
            self.logger.error(f"Error in parsing data: {e}")
            exit(-1)

    def __convert_date_paid(self, date_paid):
        self.logger.debug(f"Converting date_paid: {date_paid}")
        try:
            if date_paid:
                return date_paid.strftime("%Y-%m-%d")
            else:
                return None
        except AttributeError as e:
            self.logger.error(f"Could not convert date_paid: {e}")
            return None

    def __convert_treatments_date(self, treatments_date):
        try:
            self.logger.debug(f"The type of treatments_date is: {type(treatments_date)}")

            if isinstance(treatments_date, datetime):
                treatments_date = treatments_date.strftime('%m/%d/%Y')

            if not isinstance(treatments_date, str):
                self.logger.error("treatments_date is not a string")
                exit(-1)

            # Split the dates and format them
            dates = treatments_date.split(',')
            formatted_dates = [datetime.strptime(date.strip(), '%m/%d/%Y').strftime('%Y-%m-%d') for date in dates]
        except Exception as e:
            formatted_dates = []
            self.logger.error(f"An error occurred while converting treatment dates: {e}")
        self.logger.debug(f"number of treatments: {len(formatted_dates)}")
        return formatted_dates

    def __get_payment_method(self, bit, paybox, eft):
        if bit:
            self.payment_method = PaymentType.PAYMENT_APP
            self.app_number = 1
        elif paybox:
            self.payment_method = PaymentType.PAYMENT_APP
            self.app_number = 3
        elif eft:
            self.payment_method = PaymentType.ELECTRONIC_FUND_TRANSFER

        else:
            self.logger.error("No payment method found")
            exit(-1)

    def __construct_income_list(self):
        income_list = []
        for i in range(int(self.number_of_treatments)):
            description = f"Physiotherapy - {self.treatments[i]}"
            income_list.append(
                {
                    "catalogNum": "Physiotherapy session",
                    'description': description,
                    'quantity': 1,
                    'price': self.amount_paid / self.number_of_treatments,
                    'currency': Currency.ILS,
                    'vatType': 1,
                }
            )
        return income_list

    def __construct_payment_details(self):

        price = self.amount_paid

        payment_details = {
            'date': self.date_paid,
            'type': self.payment_method,
            'price': price,
            'currency': Currency.ILS,
            'dueDate': self.date_paid,
        }

        if self.payment_method == PaymentType.PAYMENT_APP:
            if self.app_number == 1:
                payment_details.update({
                    'appType': 1
                })
            elif self.app_number == 3:
                payment_details.update({
                    'appType': 3
                })
        elif self.payment_method == PaymentType.ELECTRONIC_FUND_TRANSFER:
            payment_details.update({
                'bankName': str(self.bank_details[0]),
                'bankBranch': str(self.bank_details[1]),
                'bankAccount': str(self.bank_details[2]),
            })
        else:
            self.logger.error(f"Unknown payment method: {self.payment_method}")
            exit(-1)
        return [payment_details]

    def __read_cred(self, file_path="Samples/Credentials.yml"):
        try:
            with open(file_path, 'r') as f:
                creds = yaml.safe_load(f)

            key = creds.get('key')
            secret = creds.get('secret')

            return key, secret
        except FileNotFoundError as fileNotFoundErr:
            self.logger.error(f"error in opening cred file: {fileNotFoundErr}")
            exit(-1)
        except:
            self.logger.error(f"Unexpected error in opening file: {file_path}")
            exit(-1)


if __name__ == "__main__":
    args = get_cli_args()
    app = InvoiceApp(command=args.command, file_path=args.file)
