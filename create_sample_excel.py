import pandas as pd
from datetime import datetime

# Sample data
data = {
    'Client': ['John Doe'],
    'Date Paid': [datetime(2024, 3, 7)],
    'Amount Paid': [500],
    'Number of Apts': [2],
    'Treatment': ['03/07/2024,03/08/2024'],
    'Bank': ['Bank Leumi'],
    'Bank Branch ': [123],
    'Account #': [456789],
    'Invoice': [False],
    'Bit': [True],
    'Paybox': [False],
    'EFT': [False],
    'Cash': [False]
}

# Create DataFrame
df = pd.DataFrame(data)

# Create Excel writer object
with pd.ExcelWriter('Samples/sample_data.xlsx', engine='openpyxl') as writer:
    # Write DataFrame to Excel
    df.to_excel(writer, sheet_name='EFT & Paybox', index=False)

print("Sample Excel file created successfully.") 