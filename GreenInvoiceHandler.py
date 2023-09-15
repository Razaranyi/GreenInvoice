import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from green_invoice.models import Currency, DocumentLanguage, DocumentType, PaymentCardType, PaymentDealType, PaymentType, IncomeVatType
from logger import Logger

logger = Logger.get_logger(__name__)


class GreenInvoiceHandler:
    BASE_URL = 'https://api.greeninvoice.co.il/api/v1'
    INVOICE_DOC_NUMBER = 320

    def __init__(self, key, secret):
        self.JWT = None
        self.status = None
        self.key = key
        self.secret = secret

    def send_POST_request(self, headers, end_point, values, request_type):
        global response_body
        data = json.dumps(values).encode('utf-8')  # Convert the dictionary to a JSON string and then encode it to bytes
        logger.info("Sending {} request; URL: {}{}, Values: {}".format(request_type, self.BASE_URL, end_point, values))
        try:
            request = Request(self.BASE_URL + end_point, data=data, headers=headers)
            response_body = urlopen(request).read()
            response = urlopen(request)
            status = response.status
            if status == 200:
                logger.info(response_body)
                pass
        except HTTPError as err:
            logger.error(err)
            logger.error(response_body)
            exit(-1)
        return json.loads(response_body)  # Parse the JSON response and return

    def generate_token(self):
        end_point = '/account/token'
        values = {
            'id': self.key,
            'secret': self.secret
        }

        headers = {
            'Content-Type': 'application/json'
        }
        parsed_response = self.send_POST_request(headers, end_point, values, "JWT")

        self.JWT = parsed_response['token']

    def search_client_by_name(self, name):
        end_point = '/clients/search'
        logger.info("Handling {}".format(name))

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
            parsed_response = self.send_POST_request(headers, end_point, values, "client search")
            total_value = parsed_response['total']
            if total_value == 0:
                raise RuntimeError
            else:
                # elif total_value == 1:
                logger.debug("client {}, found total {} client".format(name, total_value))
                first_item = parsed_response['items'][0]
                id_value = first_item['id']
                logger.debug("Parsed id of {} is: {}".format(name, id_value))
                self.generate_new_invoice(id_value)
                pass
            # else:
            #     logger.warning("Found {} clients under the name {}".format(total_value, name))
        except RuntimeError:
            logger.error("Client: {} was not found".format(name))

    def generate_new_invoice(self, id_value):
        end_point = '/documents/preview'
        values = {
            'description': 'פיזיותרפיה',
            # 'remarks': 'mock env',
            # 'email': 'example@Raz.Aranyi',
            'type': DocumentType.TAX_INVOICE_RECEIPT,
            # 'date': '2023-07-07',
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

            'income': [
                {
                    'description': 'physo',
                    'quantity': 1,
                    'price': 300,
                    'currency': Currency.ILS,
                    'vatType': 1,
                }
                   ],
            'payment': [
                {
                    'date': '2023-07-07',
                    'type': PaymentType.PAYMENT_APP,
                    'price': 300,
                    'currency': Currency.ILS,
                    'dueDate': '2023-07-14',
                    'appType': 3
                }
                ],
        }

        headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + self.JWT
            }

        response_body = self.send_POST_request(headers, end_point, values, "preview")
