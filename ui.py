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
        
        # Input field state
        self.is_placeholder = True
        self.placeholder_text = ""

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
        """Configure ttk styles with modern design."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Modern color palette
        self.colors = {
            'bg_primary': '#1e1e2e',      # Dark background
            'bg_secondary': '#2a2a40',    # Slightly lighter dark
            'bg_tertiary': '#363654',     # Card backgrounds
            'accent': '#6366f1',          # Modern indigo accent
            'accent_hover': '#4f46e5',    # Darker accent for hover
            'text_primary': '#f8fafc',    # Light text
            'text_secondary': '#cbd5e1',  # Muted text
            'success': '#10b981',         # Green for success states
            'warning': '#f59e0b',         # Orange for warnings
            'error': '#ef4444',           # Red for errors
            'border': '#475569'           # Border color
        }

        # Configure modern styles
        style.configure("TFrame", 
                       background=self.colors['bg_primary'],
                       borderwidth=0)
        
        style.configure("Modern.TLabel", 
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'],
                       font=("Inter", 10))
        
        style.configure("Heading.TLabel",
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'],
                       font=("Inter", 11, "bold"))
        
        style.configure("Modern.TButton",
                       background=self.colors['accent'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(12, 8),
                       font=("Inter", 9, "bold"))
        
        style.map("Modern.TButton",
                 background=[('active', self.colors['accent_hover']),
                           ('pressed', self.colors['accent_hover'])])
        
        style.configure("Secondary.TButton",
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_secondary'],
                       borderwidth=1,
                       relief='solid',
                       bordercolor=self.colors['border'],
                       focuscolor='none',
                       padding=(10, 6),
                       font=("Inter", 9))
        
        style.map("Secondary.TButton",
                 background=[('active', self.colors['bg_secondary']),
                           ('pressed', self.colors['bg_secondary'])])
        
        style.configure("Modern.TLabelframe",
                       background=self.colors['bg_primary'],
                       borderwidth=1,
                       relief='solid',
                       bordercolor=self.colors['border'],
                       padding=16)
        
        style.configure("Modern.TLabelframe.Label",
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'],
                       font=("Inter", 10, "bold"))
        
        style.configure("Modern.TEntry",
                       borderwidth=1,
                       relief='solid',
                       bordercolor=self.colors['border'],
                       fieldbackground=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'],
                       insertcolor=self.colors['text_primary'],
                       padding=8,
                       font=("Inter", 10))

    def _setup_ui(self):
        """Creates and arranges the main GUI elements."""
        self.root.title("Vibe MCP Client")
        self.root.geometry("1200x800")
        self.root.configure(background=self.colors['bg_primary'])
        self.root.minsize(800, 600)

        # --- Menubar with modern styling ---
        menubar = Menu(self.root, 
                      background=self.colors['bg_secondary'],
                      foreground=self.colors['text_primary'],
                      activebackground=self.colors['accent'],
                      activeforeground=self.colors['text_primary'])
        self.root.config(menu=menubar)
        
        config_menu = Menu(menubar, tearoff=0,
                          background=self.colors['bg_secondary'],
                          foreground=self.colors['text_primary'],
                          activebackground=self.colors['accent'],
                          activeforeground=self.colors['text_primary'])
        config_menu.add_command(label="Azure OpenAI Settings", command=self._open_azure_settings)
        menubar.add_cascade(label="Configuration", menu=config_menu)

        # --- Main Container ---
        main_frame = ttk.Frame(self.root, style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1) # Allow chat display to expand

        # --- MCP Server Connection Card ---
        connection_card = ttk.LabelFrame(main_frame, text="🔌 MCP Server Connection", 
                                       style="Modern.TLabelframe")
        connection_card.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        connection_card.columnconfigure(1, weight=1)

        # Server script row
        ttk.Label(connection_card, text="Server Script:", 
                 style="Modern.TLabel").grid(row=0, column=0, sticky=tk.W, padx=(0, 12), pady=8)
        
        self.server_entry = ttk.Entry(connection_card, textvariable=self.server_script_var, 
                                    style="Modern.TEntry")
        self.server_entry.grid(row=0, column=1, sticky=tk.EW, padx=(0, 12), pady=8)
        
        ttk.Button(connection_card, text="📁 Browse", 
                  command=self._browse_server_script,
                  style="Secondary.TButton").grid(row=0, column=2, padx=(0, 8), pady=8)

        # Action buttons row
        button_frame = ttk.Frame(connection_card, style="TFrame")
        button_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        
        ttk.Button(button_frame, text="🔗 Connect", 
                  command=self.controller.connect_mcp,
                  style="Modern.TButton").pack(side=tk.LEFT, padx=(0, 8))
        
        ttk.Button(button_frame, text="🔌 Disconnect", 
                  command=self.controller.disconnect_mcp,
                  style="Secondary.TButton").pack(side=tk.LEFT, padx=(0, 8))
        
        ttk.Button(button_frame, text="🛠️ List Tools", 
                  command=self.controller.list_mcp_tools,
                  style="Secondary.TButton").pack(side=tk.LEFT)

        # --- Chat Display Container ---
        chat_container = ttk.Frame(main_frame, style="TFrame")
        chat_container.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        chat_container.columnconfigure(0, weight=1)
        chat_container.rowconfigure(0, weight=1)

        # Chat display with modern styling
        self.chat_display = scrolledtext.ScrolledText(
            chat_container, 
            wrap=tk.WORD, 
            font=("Inter", 11), 
            state=tk.DISABLED,
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['text_primary'],
            selectbackground=self.colors['accent'],
            selectforeground=self.colors['text_primary'],
            bd=0,
            relief=tk.FLAT,
            padx=20,
            pady=16
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew")

        # Configure enhanced chat role tags with message bubble styling
        self.chat_display.tag_config("user", 
                                   background=self.colors['accent'],
                                   foreground=self.colors['text_primary'],
                                   font=("Inter", 11, "normal"),
                                   lmargin1=40, lmargin2=40, rmargin=20,
                                   spacing1=12, spacing3=12,
                                   borderwidth=1,
                                   relief='solid')
        
        self.chat_display.tag_config("assistant", 
                                   background=self.colors['bg_tertiary'],
                                   foreground=self.colors['text_primary'],
                                   font=("Inter", 11, "normal"),
                                   lmargin1=20, lmargin2=20, rmargin=40,
                                   spacing1=12, spacing3=12,
                                   borderwidth=1,
                                   relief='solid')
        
        self.chat_display.tag_config("system", 
                                   foreground=self.colors['text_secondary'],
                                   font=("Inter", 10, "italic"),
                                   justify=tk.CENTER,
                                   spacing1=8, spacing3=8)
        
        self.chat_display.tag_config("tool_call", 
                                   background=self.colors['warning'],
                                   foreground=self.colors['bg_primary'],
                                   font=("Consolas", 10),
                                   lmargin1=30, lmargin2=30, rmargin=30,
                                   spacing1=10, spacing3=10,
                                   borderwidth=1,
                                   relief='solid')
        
        self.chat_display.tag_config("tool_response", 
                                   background=self.colors['success'],
                                   foreground=self.colors['bg_primary'],
                                   font=("Consolas", 10),
                                   lmargin1=30, lmargin2=30, rmargin=30,
                                   spacing1=10, spacing3=10,
                                   borderwidth=1,
                                   relief='solid')


        # --- Message Input Section ---
        input_container = ttk.Frame(main_frame, style="TFrame")
        input_container.grid(row=2, column=0, sticky="ew")
        input_container.columnconfigure(0, weight=1)

        # Input frame with border styling
        input_frame = tk.Frame(input_container, 
                              bg=self.colors['bg_tertiary'],
                              relief=tk.SOLID,
                              bd=1,
                              highlightbackground=self.colors['border'],
                              highlightthickness=1)
        input_frame.pack(fill=tk.X, pady=(0, 12))
        input_frame.columnconfigure(0, weight=1)

        # Message input field with placeholder
        self.input_text = tk.Text(
            input_frame, 
            height=3, 
            font=("Inter", 11),
            bg=self.colors['bg_tertiary'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['text_primary'],
            selectbackground=self.colors['accent'],
            selectforeground=self.colors['text_primary'],
            bd=0,
            relief=tk.FLAT,
            padx=16,
            pady=12,
            wrap=tk.WORD
        )
        self.input_text.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        self.input_text.bind("<Return>", self._on_enter_pressed)
        self.input_text.bind("<Shift-Return>", self._on_shift_enter_pressed)
        
        # Add placeholder text
        self._add_placeholder_text()
        
        # Bind focus events for placeholder
        self.input_text.bind("<FocusIn>", self._on_input_focus_in)
        self.input_text.bind("<FocusOut>", self._on_input_focus_out)

        # Send button with modern styling
        send_btn = tk.Button(
            input_frame,
            text="💬 Send",
            command=self._send_input,
            bg=self.colors['accent'],
            fg=self.colors['text_primary'],
            activebackground=self.colors['accent_hover'],
            activeforeground=self.colors['text_primary'],
            font=("Inter", 10, "bold"),
            bd=0,
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        send_btn.grid(row=0, column=1, padx=(0, 12), pady=12, sticky="s")

        # --- Modern Status Bar ---
        status_frame = tk.Frame(self.root, 
                               bg=self.colors['bg_secondary'],
                               height=32)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_secondary'],
            font=("Inter", 9),
            anchor=tk.W,
            padx=20,
            pady=6
        )
        self.status_label.pack(fill=tk.BOTH, expand=True)

    def _on_enter_pressed(self, event):
        """Handles Enter key press in the input field."""
        if not self.is_placeholder:
            self._send_input()
        return "break" # Prevents the default newline insertion

    def _on_shift_enter_pressed(self, event):
        """Handles Shift+Enter key press to allow multiline input."""
        # Let the default binding handle newline insertion
        pass


    def _add_placeholder_text(self):
        """Adds placeholder text to the input field."""
        self.placeholder_text = "Type your message here... (Press Enter to send, Shift+Enter for new line)"
        self.input_text.insert("1.0", self.placeholder_text)
        self.input_text.config(fg=self.colors['text_secondary'])
        self.is_placeholder = True

    def _on_input_focus_in(self, event):
        """Removes placeholder text when input gains focus."""
        if self.is_placeholder:
            self.input_text.delete("1.0", tk.END)
            self.input_text.config(fg=self.colors['text_primary'])
            self.is_placeholder = False

    def _on_input_focus_out(self, event):
        """Adds placeholder text when input loses focus and is empty."""
        if not self.input_text.get("1.0", tk.END).strip():
            self._add_placeholder_text()

    def _send_input(self):
        """Gets text from input, clears it, and tells controller to send."""
        if self.is_placeholder:
            self.update_output("Please enter a message.", "system")
            return
            
        user_input = self.input_text.get("1.0", tk.END).strip()
        if user_input:
            self.input_text.delete("1.0", tk.END)
            self.is_placeholder = False
            # Add placeholder back
            self._add_placeholder_text()
            # Call controller method to handle the sending logic
            self.controller.send_message_to_llm(user_input)
        else:
            self.update_output("Please enter a message.", "system")


    def _browse_server_script(self):
        """Opens file dialog to select the MCP server script."""
        file_path = filedialog.askopenfilename(
            title="Select MCP Server Script",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")],
            initialfile=self.server_script_var.get()
        )
        if file_path:
            self.server_script_var.set(file_path)
            self.update_output(f"📂 Server script set to: {file_path}", "system")


    def _open_azure_settings(self):
        """Opens a modern Toplevel window for Azure configuration."""
        if hasattr(self, 'azure_window') and self.azure_window.winfo_exists():
            self.azure_window.lift()
            return

        self.azure_window = Toplevel(self.root)
        self.azure_window.title("⚙️ Azure OpenAI Configuration")
        self.azure_window.geometry("500x300")
        self.azure_window.configure(background=self.colors['bg_primary'])
        self.azure_window.transient(self.root)
        self.azure_window.grab_set()
        self.azure_window.resizable(False, False)

        # Main container
        main_container = tk.Frame(self.azure_window, bg=self.colors['bg_primary'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=24, pady=24)

        # Title
        title_label = tk.Label(
            main_container,
            text="Azure OpenAI Settings",
            bg=self.colors['bg_primary'],
            fg=self.colors['text_primary'],
            font=("Inter", 14, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 20))

        # API Key field
        self._create_settings_field(main_container, "🔑 API Key:", self.api_key_var, show="*")
        
        # Endpoint field  
        self._create_settings_field(main_container, "🌐 Endpoint:", self.endpoint_var)
        
        # Deployment field
        self._create_settings_field(main_container, "🚀 Deployment:", self.deployment_var)

        # Button container
        button_container = tk.Frame(main_container, bg=self.colors['bg_primary'])
        button_container.pack(fill=tk.X, pady=(20, 0))

        # Apply button
        apply_btn = tk.Button(
            button_container,
            text="✅ Apply Settings",
            command=self._apply_azure_settings,
            bg=self.colors['accent'],
            fg=self.colors['text_primary'],
            activebackground=self.colors['accent_hover'],
            activeforeground=self.colors['text_primary'],
            font=("Inter", 10, "bold"),
            bd=0,
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        apply_btn.pack(side=tk.RIGHT)

        # Cancel button
        cancel_btn = tk.Button(
            button_container,
            text="❌ Cancel",
            command=lambda: self.azure_window.destroy(),
            bg=self.colors['bg_tertiary'],
            fg=self.colors['text_secondary'],
            activebackground=self.colors['bg_secondary'],
            activeforeground=self.colors['text_primary'],
            font=("Inter", 10),
            bd=0,
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        cancel_btn.pack(side=tk.RIGHT, padx=(0, 12))

    def _create_settings_field(self, parent, label_text, text_var, show=None):
        """Creates a modern settings field with label and entry."""
        field_frame = tk.Frame(parent, bg=self.colors['bg_primary'])
        field_frame.pack(fill=tk.X, pady=(0, 16))

        # Label
        label = tk.Label(
            field_frame,
            text=label_text,
            bg=self.colors['bg_primary'],
            fg=self.colors['text_primary'],
            font=("Inter", 10, "bold"),
            anchor=tk.W
        )
        label.pack(anchor=tk.W, pady=(0, 6))

        # Entry
        entry = tk.Entry(
            field_frame,
            textvariable=text_var,
            bg=self.colors['bg_tertiary'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['text_primary'],
            selectbackground=self.colors['accent'],
            selectforeground=self.colors['text_primary'],
            font=("Inter", 10),
            bd=1,
            relief=tk.SOLID,
            highlightbackground=self.colors['border'],
            highlightthickness=1,
            highlightcolor=self.colors['accent'],
            show=show
        )
        entry.pack(fill=tk.X, ipady=8, ipadx=12)

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
        """Internal method to safely update the chat display with modern message bubbles."""
        try:
            self.chat_display.configure(state=tk.NORMAL)
            
            # Add spacing before message unless it's the first
            if self.chat_display.index("end-1c") != "1.0":
                self.chat_display.insert(tk.END, "\n\n")

            # Format message based on role with modern styling
            if role == "user":
                prefix = "You"
                message = f"🧑‍💻 {prefix}\n{text}"
                self.chat_display.insert(tk.END, message, "user")
            elif role == "assistant":
                prefix = "Assistant"
                message = f"🤖 {prefix}\n{text}"
                self.chat_display.insert(tk.END, message, "assistant")
            elif role == "system":
                message = f"ℹ️ {text}"
                self.chat_display.insert(tk.END, message, "system")
            elif role == "tool_call":
                message = f"🛠️ Tool Call\n{text}"
                self.chat_display.insert(tk.END, message, "tool_call")
            elif role == "tool_response":
                message = f"✅ Tool Response\n{text}"
                self.chat_display.insert(tk.END, message, "tool_response")
            else:
                # Fallback for unknown roles
                self.chat_display.insert(tk.END, text, "system")

            self.chat_display.see(tk.END)
            self.chat_display.configure(state=tk.DISABLED)
        except tk.TclError as e:
            print(f"Tkinter TclError updating output (window closed?): {e}")
        except Exception as e:
            print(f"Unexpected error updating output: {e}")


    def update_status(self, text):
        """Updates the status bar text with modern icon support."""
        # Add status icons for common states
        status_icons = {
            'ready': '✅',
            'connecting': '🔄',
            'connected': '🔗',
            'disconnected': '🔌',
            'error': '❌',
            'warning': '⚠️',
            'processing': '⚙️'
        }
        
        # Try to match status text to add appropriate icon
        text_lower = text.lower()
        icon = ''
        for key, emoji in status_icons.items():
            if key in text_lower:
                icon = f"{emoji} "
                break
        
        formatted_text = f"{icon}{text}"
        self.root.after(0, self.status_var.set, formatted_text)

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