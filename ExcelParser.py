import openpyxl

def parse_excel(file_path, sheet_name):
    wb = openpyxl.load_workbook(file_path)
    sheet = wb[sheet_name]  # Access the sheet by name

    data = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        client = {
            'Client': row[0],
            'Date Treated': row[1],
            'Amount Owed': row[2],
            'Payment Received': row[3],
            'Date Paid': row[4],
            'Paybox': row[5],
            'Bit': row[6],
            'EFT': row[7],
            'Invoice': row[8]
        }
        data.append(client)

    return data