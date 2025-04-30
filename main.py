from GreenInvoiceHandler import GreenInvoiceHandler
from invoiceApp import InvoiceApp, get_cli_args
from logger import Logger


def main():
    args = get_cli_args()
    invoiceApp = InvoiceApp(command=args.command, file_path=args.file)
    result = invoiceApp.run()
    
    if isinstance(result, set) and result:  # If we have missing clients
        print("\nMissing clients found:")
        for client in result:
            print(f"- {client}")
        
        answer = input("\nWould you like to add these clients? (yes/no): ")
        if answer.lower() == 'yes':
            for client in result:
                print(f"Adding client: {client}")
                invoiceApp.handle_missing_clients(client)
            print("\nAll clients have been added. Please run the check again.")


if __name__ == '__main__':
    main()
