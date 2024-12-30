import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from invoiceApp import InvoiceApp
from logger import Logger


class InvoiceAppGUI:
    def __init__(self, root):
        self.logger = Logger.get_logger(__name__)
        self.root = root
        root.title("Invoice Application")

        tk.Label(root, text="Select file:").pack()
        self.filename = tk.StringVar()
        tk.Entry(root, textvariable=self.filename).pack()
        tk.Button(root, text="Browse", command=self.browse_file).pack()

        self.mode = tk.StringVar(value="checkClient")
        modes = ['checkClient', 'preview', 'generate']
        tk.Label(root, text="Choose mode:").pack()
        for mode in modes:
            tk.Radiobutton(root, text=mode, variable=self.mode, value=mode).pack()

        tk.Button(root, text="Run", command=self.run_mode).pack()

        self.progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="indeterminate")
        self.progress_bar.pack(pady=20)

        self.invoice_app = None

        self.logger.debug("InvoiceAppGUI initialized")

    def browse_file(self):
        file = filedialog.askopenfilename()
        self.logger.debug(f"Selected file: {file}")
        if file:
            self.filename.set(file)

    def run_mode(self):
        file = self.filename.get()
        mode = self.mode.get()
        self.logger.debug(f"Run mode started with file: {file}, mode: {mode}")
        if not file or not mode:
            messagebox.showerror("Error", "Please select a file and a mode")
            return
        threading.Thread(target=self.start_task, args=(mode, file), daemon=True).start()

    def start_task(self, mode, file):
        self.logger.debug(f"Starting task with mode: {mode}, file: {file}")
        self.progress_bar.start()
        self.invoice_app = InvoiceApp(mode, file)
        result = self.invoice_app.run()
        self.logger.debug(f"Task completed with result: {result}")
        self.root.after(0, self.handle_result, mode, result)
        self.progress_bar.stop()

    def handle_result(self, mode, result):
        self.logger.debug(f"Handling result with mode: {mode}, result: {result}")
        if mode == 'checkClient':
            if result:
                missing_clients_str = "\n".join(result)
                if messagebox.askyesno("Missing Clients",
                                       f"These clients are missing:\n{missing_clients_str}\nDo you want to add them?"):
                    for missing_client in result:
                        self.invoice_app.handle_missing_clients(missing_client)
        else:
            messagebox.showinfo("Result", result)


def center_window(root, width=600, height=400):
    screen_width = root.winfo_screenwidth()
    # Get screen width and height
    screen_height = root.winfo_screenheight()

    # Calculate x and y coordinates
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2

    # Set the window's geometry
    root.geometry(f'{width}x{height}+{x}+{y}')


root = tk.Tk()
center_window(root)  # Centers the window with 600x400 size
app = InvoiceAppGUI(root)
root.mainloop()
