from enum import Enum

class Currency(Enum):
    ILS = 'ILS'
    USD = 'USD'
    EUR = 'EUR'

class PaymentType(Enum):
    CASH = 'cash'
    ELECTRONIC_FUND_TRANSFER = 'bank'
    PAYMENT_APP = 'payment_app'

class DocumentLanguage(Enum):
    ENGLISH = 'en'
    HEBREW = 'he'

class DocumentType(Enum):
    TAX_INVOICE_RECEIPT = 320  # Based on INVOICE_DOC_NUMBER in GreenInvoiceHandler 