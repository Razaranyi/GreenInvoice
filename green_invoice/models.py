from enum import Enum

class Currency(str, Enum):
    ILS = "ILS"
    USD = "USD"
    EUR = "EUR"

class DocumentLanguage(str, Enum):
    HEBREW = "he"
    ENGLISH = "en"

class DocumentType(str, Enum):
    INVOICE = 320
    RECEIPT = 305
    TAX_INVOICE_RECEIPT = 330

class PaymentType(str, Enum):
    CASH = 1
    CHECK = 2
    CREDIT_CARD = 3
    BANK_TRANSFER = 4
    ELECTRONIC_FUND_TRANSFER = 5
    PAYMENT_APP = 10 