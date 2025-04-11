# main.py
import asyncio
import tkinter as tk
from controller import AppController # Import the controller

# --- Async Tkinter Loop Helper ---
# Simple async loop integration. For more complex apps, consider libraries
# like 'async-tkinter-loop' or 'quamash' if needed, but this often suffices.
async def async_tkinter_loop(root):
    """Runs the Tkinter main loop in an async-compatible way."""
    while True:
        try:
            # Process Tkinter events without blocking
            root.update()
            # Yield control to the asyncio event loop
            await asyncio.sleep(0.03) # Adjust sleep time as needed (30-50ms is common)
        except tk.TclError as e:
             # Handle window closure gracefully
             if "application has been destroyed" in str(e):
                 print("Tkinter window closed.")
                 break
             else:
                 print(f"Unhandled TclError: {e}")
                 break # Exit on other Tcl errors
        except Exception as e:
             print(f"Error in async_tkinter_loop: {e}")
             break # Exit on other errors


# --- Main Application Setup ---
def main():
    """Sets up and runs the application."""
    root = tk.Tk()
    controller = AppController(root) # Create the controller, which creates the GUI

    # Start the combined Tkinter and asyncio loop
    try:
        print("Starting application loop...")
        asyncio.run(async_tkinter_loop(root))
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
    finally:
        print("Application shutting down.")
        # Perform any cleanup if necessary (e.g., ensure MCP connection is closed)
        # Note: The MCP connection *should* be handled by its context manager
        # or the disconnect logic, but final checks can be added here.
        # Example: Check if mcp_handler task is running and cancel it
        if controller.mcp_handler._connection_task and not controller.mcp_handler._connection_task.done():
             print("Cancelling active MCP connection task...")
             controller.mcp_handler._connection_task.cancel()
             # Give it a moment to process cancellation (optional)
             # asyncio.run(asyncio.sleep(0.1))


if __name__ == "__main__":
    main()