import sys
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
                           QFileDialog, QMessageBox, QLabel, QHeaderView, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor
from invoiceApp import InvoiceApp
from datetime import datetime

class CheckBoxWidget(QWidget):
    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(checked)
        layout.addWidget(self.checkbox)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def isChecked(self):
        return self.checkbox.isChecked()

class CustomTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ActionsContextMenu)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_V and (event.modifiers() & Qt.ControlModifier):
            self.paste_clipboard()
        elif event.key() == Qt.Key_C and (event.modifiers() & Qt.ControlModifier):
            self.copy_selection()
        else:
            super().keyPressEvent(event)

    def copy_selection(self):
        selected = self.selectedRanges()
        if not selected:
            return

        copied_text = []
        for r in range(selected[0].topRow(), selected[0].bottomRow() + 1):
            row_text = []
            for c in range(selected[0].leftColumn(), selected[0].rightColumn() + 1):
                cell_widget = self.cellWidget(r, c)
                if isinstance(cell_widget, CheckBoxWidget):
                    value = "TRUE" if cell_widget.isChecked() else "FALSE"
                else:
                    item = self.item(r, c)
                    value = item.text() if item else ""
                row_text.append(value)
            copied_text.append("\t".join(row_text))
        
        clipboard = QApplication.clipboard()
        clipboard.setText("\n".join(copied_text))

    def paste_clipboard(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        
        if not text:
            return

        current_row = self.currentRow()
        current_col = self.currentColumn()
        
        rows = text.split("\n")
        for i, row in enumerate(rows):
            if current_row + i >= self.rowCount():
                break
                
            cols = row.split("\t")
            for j, value in enumerate(cols):
                if current_col + j >= self.columnCount():
                    break
                    
                target_col = current_col + j
                if isinstance(self.cellWidget(current_row + i, target_col), CheckBoxWidget):
                    checkbox = self.cellWidget(current_row + i, target_col)
                    checkbox.checkbox.setChecked(value.upper() == "TRUE")
                else:
                    self.setItem(current_row + i, current_col + j, QTableWidgetItem(value))

class ExcelManagerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Green Invoice Manager")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize variables
        self.df = None  # For display
        self.original_df = None  # For Excel storage
        self.current_file = None
        self.processed_rows = set()
        
        # Define format handlers
        self.excel_formats = {
            'Date Paid': lambda x: x.strftime('%m/%d/%Y') if isinstance(x, pd.Timestamp) else x,
            'Treatment': lambda x: self.format_treatment_for_excel(x),
            'Amount': lambda x: float(x) if pd.notna(x) and str(x).strip() else None,
            'Account': lambda x: str(x) if pd.notna(x) else None,
        }
        
        self.display_formats = {
            'Date Paid': lambda x: pd.to_datetime(x).strftime('%m/%d/%Y') if pd.notna(x) else "",
            'Treatment': lambda x: self.format_treatment_for_display(x),
            'Amount': lambda x: f"{float(x):.2f}" if pd.notna(x) and str(x).strip() else "",
            'Account': lambda x: str(x) if pd.notna(x) else "",
        }
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create buttons layout
        button_layout = QHBoxLayout()
        
        # Create buttons
        self.load_button = QPushButton("Load Excel")
        self.save_button = QPushButton("Save Excel")
        self.add_row_button = QPushButton("Add Row")
        self.check_clients_button = QPushButton("Check Clients")
        self.process_button = QPushButton("Process Invoices")
        
        # Add buttons to layout
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.add_row_button)
        button_layout.addWidget(self.check_clients_button)
        button_layout.addWidget(self.process_button)
        
        # Create table
        self.table = CustomTableWidget()
        
        # Add widgets to main layout
        layout.addLayout(button_layout)
        layout.addWidget(self.table)
        
        # Connect signals
        self.load_button.clicked.connect(self.load_excel)
        self.save_button.clicked.connect(self.save_excel)
        self.add_row_button.clicked.connect(self.add_row)
        self.check_clients_button.clicked.connect(self.check_clients)
        self.process_button.clicked.connect(self.process_invoices)
        
        # Initialize buttons state
        self.update_button_states(False)
    
    def update_button_states(self, enabled=True):
        """Enable/disable buttons based on whether a file is loaded"""
        self.save_button.setEnabled(enabled)
        self.add_row_button.setEnabled(enabled)
        self.check_clients_button.setEnabled(enabled)
        self.process_button.setEnabled(enabled)
    
    def parse_date(self, value):
        """Parse a value into a datetime object"""
        if pd.isna(value):
            return pd.NaT
        try:
            return pd.to_datetime(value)
        except:
            return value

    def format_treatment_for_excel(self, value):
        """Format Treatment value for Excel storage"""
        if pd.isna(value) or not str(value).strip():
            return None
        if isinstance(value, str) and ',' in value:
            # Keep comma-separated list as is
            return value
        try:
            # Format single date as mm/dd/yyyy
            date_val = pd.to_datetime(value)
            return date_val.strftime('%m/%d/%Y')
        except:
            return str(value)

    def format_treatment_for_display(self, value):
        """Format Treatment value for display"""
        if pd.isna(value):
            return ""
        if isinstance(value, str) and ',' in value:
            # Handle multiple dates
            dates = [d.strip() for d in value.split(',')]
            formatted_dates = []
            for d in dates:
                try:
                    date_val = pd.to_datetime(d)
                    formatted_dates.append(date_val.strftime('%m/%d/%Y'))
                except:
                    formatted_dates.append(d)
            return ', '.join(formatted_dates)
        if isinstance(value, pd.Timestamp):
            return value.strftime('%m/%d/%Y')
        return str(value)

    def format_for_excel(self, value, column):
        """Format value for Excel storage"""
        if column in self.excel_formats:
            try:
                return self.excel_formats[column](value)
            except:
                return value
        return value

    def format_for_display(self, value, column):
        """Format value for display"""
        if column in self.display_formats:
            try:
                return self.display_formats[column](value)
            except:
                return str(value)
        return str(value)

    def load_excel(self):
        """Load Excel file and display in table"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open Excel File", "", "Excel Files (*.xlsx *.xls)")
        
        if file_name:
            try:
                # Read Excel file into original_df
                self.original_df = pd.read_excel(file_name, sheet_name='EFT & Paybox')
                
                # Convert dates to proper format in original_df
                if 'Date Paid' in self.original_df.columns:
                    self.original_df['Date Paid'] = pd.to_datetime(self.original_df['Date Paid']).dt.strftime('%m/%d/%Y')
                
                if 'Treatment' in self.original_df.columns:
                    self.original_df['Treatment'] = self.original_df['Treatment'].apply(
                        lambda x: pd.to_datetime(x).strftime('%m/%d/%Y') if pd.notna(x) and not isinstance(x, str) else x
                    )
                
                # Create display DataFrame
                self.df = self.original_df.copy()
                
                # Format display values
                for column in self.df.columns:
                    if column in self.display_formats:
                        self.df[column] = self.df[column].apply(self.display_formats[column])
                
                self.current_file = file_name
                self.display_data()
                self.update_button_states(True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading file: {str(e)}")
    
    def is_boolean_column(self, column_name, value=None):
        """Check if a column should be treated as boolean"""
        boolean_columns = {'Cash', 'Bit', 'Paybox', 'EFT', 'Invoice'}
        if column_name in boolean_columns:
            return True
            
        if isinstance(value, bool):
            return True
            
        if isinstance(value, str) and value.upper() in ['TRUE', 'FALSE']:
            return True
            
        return False

    def get_boolean_value(self, value):
        """Convert various value formats to boolean"""
        print(f"Converting value: {value}, type: {type(value)}")  # Debug print
        
        if pd.isna(value):
            return False
            
        if isinstance(value, bool):
            return value
            
        if isinstance(value, (int, float)):
            return bool(value)
            
        if isinstance(value, str):
            value = value.upper().strip()
            if value in ['TRUE', '1', 'YES', 'Y']:
                return True
            if value in ['FALSE', '0', 'NO', 'N', '']:
                return False
            try:
                return bool(float(value))
            except ValueError:
                return False
                
        return False

    def format_value(self, value, column_name):
        """Format value based on column type"""
        if pd.isna(value):
            return ""
        
        # Handle boolean columns (TRUE/FALSE fields)
        if self.is_boolean_column(column_name, value):
            return "TRUE" if self.get_boolean_value(value) else "FALSE"
        
        # Use original value if available
        row_idx = self.table.currentRow()
        if hasattr(self, 'original_values') and row_idx >= 0 and row_idx < len(self.original_values):
            original_value = self.original_values.iloc[row_idx].get(column_name)
            if not pd.isna(original_value):
                return str(original_value)
        
        # Handle Treatment column - preserve exact value
        if column_name == 'Treatment':
            return str(value)
        
        # Handle Date Paid column
        if column_name == 'Date Paid':
            if isinstance(value, pd.Timestamp):
                return value.strftime('%m/%d/%Y')
            return str(value)
        
        # Handle numeric columns
        if isinstance(value, (int, float)):
            try:
                if float(value).is_integer():
                    return str(int(value))
                return f"{value:.2f}"
            except:
                return str(value)
        
        return str(value)

    def get_original_value(self, value, column_type):
        """Convert display value back to original format"""
        if pd.isna(value) or value == "":
            return pd.NA
            
        if column_type == bool:
            return value == "TRUE"
        elif pd.api.types.is_datetime64_dtype(column_type):
            return pd.to_datetime(value)
        elif pd.api.types.is_numeric_dtype(column_type):
            try:
                return float(value)
            except ValueError:
                return value
        return value

    def display_data(self):
        """Display DataFrame in table"""
        if self.df is not None:
            # Convert boolean columns to proper boolean type
            boolean_columns = {'Cash', 'Bit', 'Paybox', 'EFT', 'Invoice'}
            for col in boolean_columns:
                if col in self.df.columns:
                    # Print sample values before conversion
                    print(f"\nBefore conversion - {col} values:")
                    print(self.df[col].head())
                    
                    # Convert to boolean
                    self.df[col] = self.df[col].apply(lambda x: self.get_boolean_value(x))
                    
                    # Print sample values after conversion
                    print(f"\nAfter conversion - {col} values:")
                    print(self.df[col].head())

            # Remove empty rows (where 'Client' is empty)
            self.df = self.df.dropna(subset=['Client']).reset_index(drop=True)
            
            # Set table dimensions
            self.table.setRowCount(len(self.df))
            self.table.setColumnCount(len(self.df.columns) + 1)  # +1 for status column
            
            # Set headers
            headers = list(self.df.columns) + ["Status"]
            self.table.setHorizontalHeaderLabels(headers)
            
            # Fill data
            for i in range(len(self.df)):
                for j, column in enumerate(self.df.columns):
                    value = self.df.iloc[i][column]
                    
                    # Check if this is a boolean column
                    if column in boolean_columns:
                        is_checked = bool(value)  # Use direct boolean conversion since we already converted the values
                        print(f"Row {i}, Column {column}: Original Value = {value}, Checked = {is_checked}")  # Debug print
                        checkbox_widget = CheckBoxWidget(is_checked)
                        self.table.setCellWidget(i, j, checkbox_widget)
                    else:
                        formatted_value = self.format_value(value, column)
                        item = QTableWidgetItem(formatted_value)
                        if column == 'Client':  # Make client column bold
                            font = item.font()
                            font.setBold(True)
                            item.setFont(font)
                        self.table.setItem(i, j, item)
                
                # Add status column
                status_item = QTableWidgetItem("")
                if i in self.processed_rows:
                    status_item.setText("✓")
                    status_item.setForeground(QColor("green"))
                self.table.setItem(i, len(self.df.columns), status_item)
            
            # Adjust column widths
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    
    def save_excel(self):
        """Save changes back to Excel"""
        if self.df is not None and self.current_file:
            try:
                # Create a copy of the DataFrame to update
                display_df = self.df.copy()
                save_df = self.original_df.copy() if self.original_df is not None else pd.DataFrame(columns=self.df.columns)
                
                # Update DataFrame from table
                for i in range(self.table.rowCount()):
                    row_data = {}
                    excel_data = {}
                    for j, column in enumerate(self.df.columns):
                        # Handle checkbox widgets
                        cell_widget = self.table.cellWidget(i, j)
                        if isinstance(cell_widget, CheckBoxWidget):
                            is_checked = cell_widget.isChecked()
                            row_data[column] = "TRUE" if is_checked else "FALSE"
                            excel_data[column] = is_checked  # Store as actual boolean
                        else:
                            item = self.table.item(i, j)
                            value = item.text() if item else None
                            
                            if value is None or value == "":
                                row_data[column] = None
                                excel_data[column] = None
                            else:
                                # Format for display
                                row_data[column] = self.format_for_display(value, column)
                                # Format for Excel
                                excel_data[column] = self.format_for_excel(value, column)
                    
                    # Update both DataFrames
                    for column, value in row_data.items():
                        display_df.at[i, column] = value
                        save_df.at[i, column] = excel_data[column]
                
                # Create Excel writer with xlsxwriter engine
                writer = pd.ExcelWriter(self.current_file, engine='xlsxwriter')
                
                # Write the Excel-formatted DataFrame
                save_df.to_excel(writer, sheet_name='EFT & Paybox', index=False)
                
                # Get workbook and worksheet objects
                workbook = writer.book
                worksheet = writer.sheets['EFT & Paybox']
                
                # Define formats
                text_format = workbook.add_format({'align': 'left'})
                date_format = workbook.add_format({'num_format': 'mm/dd/yyyy'})
                number_format = workbook.add_format({'num_format': '0'})
                
                # Set column formats
                for idx, col in enumerate(save_df.columns):
                    if col == 'Client':
                        worksheet.set_column(idx, idx, None, text_format)
                    elif col in {'Date Paid', 'Treatment'}:
                        worksheet.set_column(idx, idx, None, date_format)
                    elif col in {'Amount', 'Account'}:
                        worksheet.set_column(idx, idx, None, number_format)
                    else:
                        worksheet.set_column(idx, idx, None, None)
                
                # Save and close
                writer.close()
                
                # Update our DataFrames
                self.original_df = save_df
                self.df = display_df
                
                QMessageBox.information(self, "Success", "File saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving file: {str(e)}")
    
    def add_row(self):
        """Add new empty row to table"""
        if self.df is not None:
            current_row = self.table.rowCount()
            self.table.insertRow(current_row)
            
            # Create empty row with correct data types
            new_row_data = {}
            new_row_excel_data = {}
            
            for column in self.df.columns:
                if column in {'Cash', 'Bit', 'Paybox', 'EFT', 'Invoice'}:
                    new_row_data[column] = "FALSE"
                    new_row_excel_data[column] = False
                else:
                    new_row_data[column] = ""
                    new_row_excel_data[column] = None
            
            # Add empty cells to table
            for j, column in enumerate(self.df.columns):
                if column in {'Cash', 'Bit', 'Paybox', 'EFT', 'Invoice'}:
                    checkbox_widget = CheckBoxWidget(False)
                    self.table.setCellWidget(current_row, j, checkbox_widget)
                else:
                    self.table.setItem(current_row, j, QTableWidgetItem(""))
            
            # Add empty status cell
            self.table.setItem(current_row, len(self.df.columns), QTableWidgetItem(""))
            
            # Update both DataFrames
            new_row_df = pd.DataFrame([new_row_data])
            self.df = pd.concat([self.df, new_row_df], ignore_index=True)
            
            new_row_excel_df = pd.DataFrame([new_row_excel_data])
            if self.original_df is None:
                self.original_df = new_row_excel_df
            else:
                self.original_df = pd.concat([self.original_df, new_row_excel_df], ignore_index=True)
    
    def check_clients(self):
        """Check clients using InvoiceApp"""
        if self.current_file:
            try:
                self.save_excel()  # Save current changes
                invoice_app = InvoiceApp(command="checkClient", file_path=self.current_file)
                result = invoice_app.run()
                
                if isinstance(result, set) and result:
                    missing_clients = "\n".join([f"- {client}" for client in result])
                    reply = QMessageBox.question(self, "Missing Clients",
                        f"The following clients are missing:\n{missing_clients}\n\nWould you like to add them?",
                        QMessageBox.Yes | QMessageBox.No)
                    
                    if reply == QMessageBox.Yes:
                        for client in result:
                            invoice_app.handle_missing_clients(client)
                        QMessageBox.information(self, "Success", "All clients have been added!")
                else:
                    QMessageBox.information(self, "Success", "All clients are valid!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error checking clients: {str(e)}")
    
    def process_invoices(self):
        """Process invoices using InvoiceApp"""
        if self.current_file:
            try:
                # Save current changes first
                self.save_excel()
                
                # Create InvoiceApp instance with generate command
                invoice_app = InvoiceApp(command="generate", file_path=self.current_file)
                result = invoice_app.run()
                
                # Check if any invoices were processed
                if result is True:  # generate command returns True on success
                    # Mark all non-invoiced rows as processed
                    for i in range(self.table.rowCount()):
                        invoice_cell = self.table.cellWidget(i, self.df.columns.get_loc('Invoice'))
                        if invoice_cell and not invoice_cell.isChecked():
                            self.processed_rows.add(i)
                    
                    # Refresh the display to show checkmarks
                    self.display_data()
                    QMessageBox.information(self, "Success", "Invoices processed successfully!")
                else:
                    QMessageBox.warning(self, "Warning", "No invoices were processed.")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error processing invoices: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = ExcelManagerUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 