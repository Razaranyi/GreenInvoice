import base64
import json
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from green_invoice.models import Currency, DocumentLanguage, DocumentType

from logger import Logger


class GreenInvoiceHandler:
    BASE_URL = 'https://api.greeninvoice.co.il/api/v1'
    INVOICE_DOC_NUMBER = 320

    def __init__(self, key, secret):
        self.JWT = None
        self.status = None
        self.key = key
        self.secret = secret
        self.logger = Logger.get_logger(__name__)

    def __send_POST_request(self, headers, end_point, values, request_type):
        global response_body
        data = json.dumps(values).encode('utf-8')
        self.logger.info(
            f"Sending {request_type} request; URL: {self.BASE_URL}{end_point}, Values: {values}")
        try:
            request = Request(self.BASE_URL + end_point, data=data, headers=headers)
            response = urlopen(request)  # Store the response object in a variable
            response_body = response.read()  # Read the response body from the response object
            status = response.status  # Get the status from the response object
            if status == 200:
                if request_type != "preview":
                    self.logger.info(f"Response body: {response_body}")
                    pass
        except HTTPError as err:
            self.logger.error(err)
            self.logger.error(response_body)
            exit(-1)
        return json.loads(response_body)


    def generate_token(self):
        end_point = '/account/token'
        values = {
            'id': self.key,
            'secret': self.secret
        }

        headers = {
            'Content-Type': 'application/json'
        }
        parsed_response = self.__send_POST_request(headers, end_point, values, "JWT")

        self.JWT = parsed_response['token']

    def search_client_by_name(self, name):
        end_point = '/clients/search'
        values = {
            'name': name,
            'active': 'true',
            'page': 1,
            'pageSize': 5
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.JWT
        }
        try:
            parsed_response = self.__send_POST_request(headers, end_point, values, "client search")
            total_value = parsed_response['total']
            if total_value == 0:
                return None

            elif total_value == 1:
                self.logger.debug(f"client {name}, found total {total_value} client")
                first_item = parsed_response['items'][0]
                id_value = first_item['id']
                self.logger.debug(f"Parsed id of {name} is: {id_value}")
                return id_value
                pass
            else:
                self.logger.warning(f"Found {total_value} clients under the name {name}")
                return None
        except RuntimeError as err:
            self.logger.error(f"Error in finding client: {err}")
            return None

    def generate_new_invoice_preview(self, parsed_values, client_name):
        print(f"Generating preview for {client_name}")
        end_point = '/documents/preview'
        values = parsed_values

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.JWT
        }
        response_body = self.__send_POST_request(headers, end_point, values, "preview")
        if 'file' in response_body:
            time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.__base64_to_pdf(response_body['file'], f"Samples/Invoices/{client_name}_{time_stamp}_Invoice.pdf")
        else:
            self.logger.error("'file' key does not exist in the response body.")

    def generate_new_invoice(self, parsed_values, client_name):
        print(f"Generating invoice for {client_name}")
        end_point = '/documents'
        values = parsed_values

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.JWT
        }
        response_body = self.__send_POST_request(headers, end_point, values, "generate")
        self.logger.debug(f"response_body: {response_body}")

    def parse_values(self, id_value, payment_details, payment_date, income_list):

        values = {

            'type': DocumentType.TAX_INVOICE_RECEIPT,
            'date': payment_date,
            'lang': DocumentLanguage.ENGLISH,
            'currency': Currency.ILS,
            'vatType': 0,
            'discount':
                {
                    'amount': 0,
                    'type': "sum",
                },
            'client':
                {
                    'id': id_value,
                },

            'income': income_list,
            'payment': payment_details,
        }
        self.logger.debug(f"Values: {values}")

        return values

    def __base64_to_pdf(self, base64_data, output_filepath):
        try:
            decoded_data = base64.b64decode(base64_data)

            with open(output_filepath, 'wb') as file:
                file.write(decoded_data)

            self.logger.info(f"The preview PDF has been successfully saved at {output_filepath}")
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
