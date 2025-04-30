import yaml
import argparse
from datetime import datetime
from green_invoice.models import Currency, PaymentType, DocumentType
from ExcelParser import ExcelParser
from GreenInvoiceHandler import GreenInvoiceHandler
from logger import Logger


def get_cli_args():
    parser = argparse.ArgumentParser(description='Invoice App CLI')
    parser.add_argument('command', choices=['checkClient', 'preview', 'generate'], help='Command to execute')
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

        self.client_name = None
        self.date_paid = None
        self.amount_paid = None
        self.number_of_treatments = None
        self.treatments = None
        self.payment_method = None
        self.invoice = None
        self.bank_details = None
        self.app_number = None

        # self.run()

    def run(self):
        missing_clients = set()
        for row_index, row_data in enumerate(self.file.data):
            self.logger.debug(f"Starting row {row_index}")
            self.__load_row_data(row_index)
            self.logger.debug(f"Parsed {self.client_name} row")

            # Only skip invoiced rows for preview and generate commands
            if self.invoice and self.command != 'checkClient':
                if self.allow_skips:
                    self.logger.debug(f"Skipping invoice {self.invoice}")
                    continue
                else:
                    self.logger.critical(f"Invoice {self.invoice} already issued. Exit script")
                    exit(-1)

            result = self.green_invoice_client.search_client_by_name(self.client_name)
            if result:
                client_id, client_email = result
            else:
                client_id, client_email = None, None

            if client_id is None:
                self.logger.warning(f"Client {self.client_name} not found")
                missing_clients.add(self.client_name)
                if self.command != 'checkClient':
                    exit(-1)

            else:
                income_list = self.__construct_income_list()
                payment_details = self.__construct_payment_details()
                values = self.green_invoice_client.parse_values(client_id, payment_details, self.date_paid,
                                                                income_list, client_email)

                if self.command == 'preview':
                    self.green_invoice_client.generate_new_invoice_preview(values, self.client_name)
                elif self.command == 'generate':
                    self.__handle_generate(row_index, values)
                elif self.command == 'checkClient':
                    pass
                else:
                    self.logger.error(f"Unknown command: {self.command}")
                    print(f"Unknown command: {self.command}. Exiting...")
                    exit(-1)
        if missing_clients:
            return missing_clients
        else:
            self.logger.info("Finished processing all rows")
            return self.command + " completed successfully"

    def __handle_generate(self, row_index, values):
        self.green_invoice_client.generate_new_invoice(values, self.client_name)
        self.file.change_invoice_status(row_index)
        self.allow_skips = False
        self.logger.debug(f"Allowing skips: {self.allow_skips}")

    def handle_missing_clients(self, missing_clients):
        self.green_invoice_client.add_client(missing_clients)

    def __load_row_data(self, row_index):
        try:
            row_data = self.file.get_row(row_index)
        except Exception as e:
            self.logger.error(f"Error in parsing data: {e}")
            exit(-1)
        try:
            # Get client name
            self.client_name = self.file.get_cell(row_data, 'Client')
            if not self.client_name:
                self.logger.error(f"Missing client name in row {row_index}")
                exit(-1)

            # Get and convert date paid
            date_paid_raw = self.file.get_cell(row_data, 'Date Paid')
            if not date_paid_raw:
                self.logger.error(f"Missing date paid in row {row_index}")
                exit(-1)
            self.date_paid = self.__convert_date_paid(date_paid_raw)
            if not self.date_paid:
                self.logger.error(f"Invalid date paid format in row {row_index}")
                exit(-1)

            # Get and convert amount paid
            amount_paid = self.file.get_cell(row_data, 'Amount Paid')
            if not amount_paid:
                self.logger.error(f"Missing amount paid in row {row_index}")
                exit(-1)
            try:
                self.amount_paid = float(amount_paid)
            except (ValueError, TypeError):
                msg = f"Invalid amount paid format in row {row_index}: {amount_paid}"
                self.logger.error(msg)
                exit(-1)

            # Get and convert number of treatments
            num_apts = self.file.get_cell(row_data, 'Number of Apts')
            if not num_apts:
                self.logger.error(f"Missing number of treatments in row {row_index}")
                exit(-1)
            try:
                self.number_of_treatments = int(num_apts)
                if self.number_of_treatments <= 0:
                    msg = f"Number of treatments must be positive in row {row_index}"
                    self.logger.error(msg)
                    exit(-1)
            except (ValueError, TypeError):
                msg = f"Invalid number of treatments in row {row_index}: {num_apts}"
                self.logger.error(msg)
                exit(-1)

            # Get and convert treatments
            treatments_raw = self.file.get_cell(row_data, 'Treatment')
            if not treatments_raw:
                self.logger.error(f"Missing treatment dates in row {row_index}")
                exit(-1)
            self.treatments = self.__convert_treatments_date(treatments_raw)
            if not self.treatments:
                self.logger.error(f"Invalid treatment dates format in row {row_index}")
                exit(-1)
            if len(self.treatments) != self.number_of_treatments:
                msg = (f"Number of treatment dates ({len(self.treatments)}) does not "
                      f"match number of treatments ({self.number_of_treatments}) "
                      f"in row {row_index}")
                self.logger.error(msg)
                exit(-1)

            # Get bank details
            bank = self.file.get_cell(row_data, 'Bank')
            branch = self.file.get_cell(row_data, 'Bank Branch ')
            account = self.file.get_cell(row_data, 'Account #')
            self.bank_details = [bank, branch, account]

            # Get invoice status and payment method
            self.invoice = self.file.get_cell(row_data, 'Invoice')
            self.__get_payment_method(row_data)

        except Exception as e:
            self.logger.error(f"Error in parsing data: {e}")
            exit(-1)

    def __convert_date_paid(self, date_paid):
        self.logger.debug(f"Converting date_paid: {date_paid}")
        try:
            if not date_paid:
                return None
                
            if isinstance(date_paid, datetime):
                return date_paid.strftime("%Y-%m-%d")
                
            try:
                # Try mm/dd/yyyy format first
                parsed = datetime.strptime(str(date_paid).strip(), '%m/%d/%Y')
            except ValueError:
                try:
                    # Try yyyy-mm-dd format
                    parsed = datetime.strptime(str(date_paid).strip(), '%Y-%m-%d')
                except ValueError:
                    msg = (f"Date paid '{date_paid}' is not in a valid format "
                          "(expected mm/dd/yyyy or yyyy-mm-dd)")
                    self.logger.error(msg)
                    return None
                    
            return parsed.strftime("%Y-%m-%d")
            
        except Exception as e:
            self.logger.error(f"Could not convert date_paid: {e}")
            return None

    def __convert_treatments_date(self, treatments_date):
        try:
            if not treatments_date:
                return []

            if isinstance(treatments_date, datetime):
                return [treatments_date.strftime('%Y-%m-%d')]

            treatments_date = str(treatments_date).strip()
            dates = [date.strip() for date in treatments_date.split(',')]
            formatted_dates = []
            
            for date in dates:
                try:
                    # Try mm/dd/yyyy format first
                    parsed = datetime.strptime(date, '%m/%d/%Y')
                except ValueError:
                    try:
                        # Try yyyy-mm-dd format
                        parsed = datetime.strptime(date, '%Y-%m-%d')
                    except ValueError:
                        msg = (f"Treatment date '{date}' is not in valid format "
                              "(expected mm/dd/yyyy or yyyy-mm-dd)")
                        self.logger.error(msg)
                        continue
                formatted_dates.append(parsed.strftime('%Y-%m-%d'))
                
            return formatted_dates
            
        except Exception as e:
            self.logger.error(f"An error occurred while converting treatment dates: {e}")
            return []

    def __get_payment_method(self, row_data):
        bit = self.file.get_cell(row_data, 'Bit')
        paybox = self.file.get_cell(row_data, 'Paybox')
        eft = self.file.get_cell(row_data, 'EFT')
        cash = self.file.get_cell(row_data, 'Cash')
        
        if bit:
            self.payment_method = PaymentType.PAYMENT_APP
            self.app_number = 1
        elif paybox:
            self.payment_method = PaymentType.PAYMENT_APP
            self.app_number = 3
        elif eft:
            self.payment_method = PaymentType.BANK_TRANSFER
        elif cash:
            self.payment_method = PaymentType.CASH
        else:
            self.logger.debug(f"name: {self.client_name}")
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

        payment_details = {
            'date': self.date_paid,
            'type': self.payment_method,
            'price': self.amount_paid,
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
        elif self.payment_method == PaymentType.BANK_TRANSFER:
            payment_details.update({
                'bankName': str(self.bank_details[0]),
                'bankBranch': str(self.bank_details[1]),
                'bankAccount': str(self.bank_details[2]),
            })
        elif self.payment_method == PaymentType.CASH:  # Cash
            pass

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

# if __name__ == "__main__":
# args = get_cli_args()
# app = InvoiceApp(command=args.command, file_path=args.file)
