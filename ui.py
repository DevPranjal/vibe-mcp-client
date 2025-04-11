# ui.py
import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog, Menu, Toplevel

class AppGUI:
    """Handles the Tkinter GUI elements and layout."""

    def __init__(self, root, controller):
        """
        Initializes the GUI.

        Args:
            root: The main Tkinter window (tk.Tk instance).
            controller: The application controller instance to handle actions.
        """
        self.root = root
        self.controller = controller

        # --- Tkinter Variables ---
        self.api_key_var = tk.StringVar()
        self.endpoint_var = tk.StringVar()
        self.deployment_var = tk.StringVar()
        self.server_script_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Initializing...")

        # --- Initialize variables from controller/config ---
        # The controller should load config and pass initial values here
        self.api_key_var.set(self.controller.get_config_value("api_key", ""))
        self.endpoint_var.set(self.controller.get_config_value("endpoint", ""))
        self.deployment_var.set(self.controller.get_config_value("deployment", ""))
        self.server_script_var.set(self.controller.get_config_value("default_server_script", "server.py"))


        self._setup_styles()
        self._setup_ui()
        self.status_var.set("Ready") # Set initial status after UI setup

    def _setup_styles(self):
        """Configure ttk styles."""
        style = ttk.Style()
        style.theme_use('clam') # Or 'alt', 'default', 'classic'

        style.configure("TFrame", background="#f5f5f5")
        style.configure("TLabel", background="#f5f5f5", font=("Segoe UI", 10))
        style.configure("TButton", padding=5, font=("Segoe UI", 10))
        style.configure("TLabelframe", background="#f5f5f5", padding=10)
        style.configure("TLabelframe.Label", background="#f5f5f5", font=("Segoe UI", 10, "bold"))
        # Add more style configurations as needed

    def _setup_ui(self):
        """Creates and arranges the main GUI elements."""
        self.root.title("MCP Client")
        self.root.geometry("900x700")
        self.root.configure(background="#f5f5f5")

        # --- Menubar ---
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        config_menu = Menu(menubar, tearoff=0)
        config_menu.add_command(label="Azure OpenAI Settings", command=self._open_azure_settings)
        # Removed MCP settings from menu as it's now inline
        menubar.add_cascade(label="Configuration", menu=config_menu)

        # --- Main Frame ---
        main_frame = ttk.Frame(self.root, style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1) # Allow chat display to expand

        # --- MCP Server Settings Frame (Inline) ---
        mcp_settings_frame = ttk.LabelFrame(main_frame, text="MCP Server Connection", padding=10)
        mcp_settings_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(0, 10))
        mcp_settings_frame.columnconfigure(1, weight=1) # Allow entry to expand

        ttk.Label(mcp_settings_frame, text="Server Script:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        ttk.Entry(mcp_settings_frame, textvariable=self.server_script_var, width=40).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        ttk.Button(mcp_settings_frame, text="Browse", command=self._browse_server_script).grid(row=0, column=2, padx=5, pady=2)
        ttk.Button(mcp_settings_frame, text="Connect", command=self.controller.connect_mcp).grid(row=0, column=3, padx=5, pady=2)
        ttk.Button(mcp_settings_frame, text="Disconnect", command=self.controller.disconnect_mcp).grid(row=0, column=4, padx=5, pady=2)
        ttk.Button(mcp_settings_frame, text="List Tools", command=self.controller.list_mcp_tools).grid(row=0, column=5, padx=5, pady=2)

        # --- Chat Display Frame ---
        chat_frame = ttk.Frame(main_frame, style="TFrame")
        chat_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)

        self.chat_display = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, font=("Consolas", 10), state=tk.DISABLED, bd=0, relief=tk.FLAT, padx=5, pady=5)
        self.chat_display.grid(row=0, column=0, sticky="nsew")

        # Configure tags for chat roles
        self.chat_display.tag_config("user", foreground="#0000AA", font=("Segoe UI", 10, "bold"))
        self.chat_display.tag_config("assistant", foreground="#007700")
        self.chat_display.tag_config("system", foreground="#880000", font=("Segoe UI", 9, "italic"))
        self.chat_display.tag_config("tool_call", foreground="#555555", font=("Consolas", 9))
        self.chat_display.tag_config("tool_response", foreground="#555555", font=("Consolas", 9))


        # --- Input Frame ---
        input_frame = ttk.Frame(main_frame, style="TFrame")
        input_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=(5, 0))
        input_frame.columnconfigure(0, weight=1)

        self.input_text = tk.Text(input_frame, height=4, font=("Segoe UI", 10), bd=1, relief=tk.SOLID)
        self.input_text.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=5)
        self.input_text.bind("<Return>", self._on_enter_pressed) # Send on Enter
        self.input_text.bind("<Shift-Return>", self._on_shift_enter_pressed) # Allow Shift+Enter for newline


        send_btn = ttk.Button(input_frame, text="Send", command=self._send_input)
        send_btn.grid(row=0, column=1, padx=(0, 5), pady=5, sticky="ns")

        # --- Status Bar ---
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, background="#007ACC", foreground="white", font=("Segoe UI", 9), padding=(5, 2))
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _on_enter_pressed(self, event):
        """Handles Enter key press in the input field."""
        self._send_input()
        return "break" # Prevents the default newline insertion

    def _on_shift_enter_pressed(self, event):
        """Handles Shift+Enter key press to allow multiline input."""
        # Let the default binding handle newline insertion
        pass


    def _send_input(self):
        """Gets text from input, clears it, and tells controller to send."""
        user_input = self.input_text.get("1.0", tk.END).strip()
        if user_input:
            self.input_text.delete("1.0", tk.END)
            # Call controller method to handle the sending logic
            self.controller.send_message_to_llm(user_input)
        else:
            self.update_output("Please enter a message.", "system")


    def _browse_server_script(self):
        """Opens file dialog to select the MCP server script."""
        file_path = filedialog.askopenfilename(
            title="Select MCP Server Script",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")],
            initialfile=self.server_script_var.get() # Start in the current dir or with current script
        )
        if file_path:
            self.server_script_var.set(file_path)
            self.update_output(f"Server script set to: {file_path}", "system")


    def _open_azure_settings(self):
        """Opens a Toplevel window for Azure configuration."""
        # Simple Toplevel for settings
        if hasattr(self, 'azure_window') and self.azure_window.winfo_exists():
            self.azure_window.lift()
            return

        self.azure_window = Toplevel(self.root)
        self.azure_window.title("Azure OpenAI Settings")
        self.azure_window.geometry("400x150")
        self.azure_window.configure(background="#f5f5f5")
        self.azure_window.transient(self.root) # Keep on top of main window
        self.azure_window.grab_set() # Modal behavior

        azure_frame = ttk.Frame(self.azure_window, padding=15)
        azure_frame.pack(fill=tk.BOTH, expand=True)
        azure_frame.columnconfigure(1, weight=1)

        ttk.Label(azure_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(azure_frame, textvariable=self.api_key_var, show="*", width=40).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)

        ttk.Label(azure_frame, text="Endpoint:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(azure_frame, textvariable=self.endpoint_var, width=40).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)

        ttk.Label(azure_frame, text="Deployment:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(azure_frame, textvariable=self.deployment_var, width=40).grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)

        # Add an OK button to apply settings (optional, could apply on change)
        ok_button = ttk.Button(azure_frame, text="OK", command=self._apply_azure_settings)
        ok_button.grid(row=3, column=0, columnspan=2, pady=10)

    def _apply_azure_settings(self):
        """Applies Azure settings and closes the settings window."""
        self.controller.update_azure_config(
            self.api_key_var.get(),
            self.endpoint_var.get(),
            self.deployment_var.get()
        )
        if hasattr(self, 'azure_window') and self.azure_window.winfo_exists():
            self.azure_window.destroy()


    # --- Public Methods for Controller to Update UI ---

    def update_output(self, text, role="system"):
        """Appends text to the chat display with specified role formatting."""
        # Ensure this runs on the main Tkinter thread
        self.root.after(0, self._update_output_thread_safe, text, role)

    def _update_output_thread_safe(self, text, role):
        """Internal method to safely update the chat display."""
        try:
            self.chat_display.configure(state=tk.NORMAL)
            # Add a newline before the message for spacing, unless it's the very first message
            if self.chat_display.index("end-1c") != "1.0":
                 self.chat_display.insert(tk.END, "\n")

            # Apply role tag - use specific tags for tool calls/responses
            if role == "tool_call" or role == "tool_response":
                 self.chat_display.insert(tk.END, text, role)
            else:
                 prefix = f"{role.capitalize()}: " if role not in ["system"] else "" # Add prefix like "User: "
                 self.chat_display.insert(tk.END, f"{prefix}{text}", role)


            self.chat_display.insert(tk.END, "\n") # Add newline after for spacing
            self.chat_display.see(tk.END) # Scroll to the bottom
            self.chat_display.configure(state=tk.DISABLED)
        except tk.TclError as e:
            print(f"Tkinter TclError updating output (window closed?): {e}")
        except Exception as e:
             print(f"Unexpected error updating output: {e}")


    def update_status(self, text):
        """Updates the status bar text."""
        # Ensure this runs on the main Tkinter thread
        self.root.after(0, self.status_var.set, text)

    def get_server_script_path(self):
        """Returns the current server script path from the UI."""
        return self.server_script_var.get()

    def get_azure_config(self):
        """Returns the current Azure config from the UI."""
        return {
            "api_key": self.api_key_var.get(),
            "endpoint": self.endpoint_var.get(),
            "deployment": self.deployment_var.get(),
        }