# src/main.py
import keyboard # For global hotkey listening
import threading # To potentially run GUI in a separate thread if needed, but pystray runs in main.
# from time import sleep # If needing to keep main alive for a non-blocking keyboard listener.
import ctypes
import tkinter as tk
from tkinter import messagebox

from src.core_logic import SuperModeManager
from src.gui import start_gui, update_icon_status # Import update_icon_status
from src.logger import default_logger as logger
from src.config import SUPER_MODE_HOTKEY

# Global reference for super_mode_manager to be accessible by hotkey callback
# This is needed because keyboard.add_hotkey callback doesn't easily pass arguments.
# Another way is to use functools.partial.
_main_super_mode_manager = None

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError: # Should not happen on Windows, but good practice
        logger.warning("Could not determine admin status via ctypes (AttributeError). Assuming not admin.")
        return False
    except Exception as e:
        logger.error(f"Error checking admin status: {e}", include_exception_info=True)
        return False # Assume not admin on error

def on_hotkey_pressed():
    global _main_super_mode_manager
    if _main_super_mode_manager:
        logger.info(f"Hotkey {SUPER_MODE_HOTKEY} pressed!")
        _main_super_mode_manager.toggle_super_mode()
        # We need to tell the GUI to update its icon
        if update_icon_status: # Call the global update_icon_status from gui.py
             update_icon_status()
        else:
             logger.warning("Hotkey: Could not find a way to trigger GUI icon update (update_icon_status not available).")

    else:
        logger.error("Hotkey pressed, but SuperModeManager reference is not set in main.")

def main():
    global _main_super_mode_manager
    logger.info("Application starting...")

    if not is_admin():
        admin_warning = "Warning: Application is not running with administrator privileges. Some features (like network/USB control, Task Manager modification, closing some apps) may not work correctly or will fail. Please restart as administrator for full functionality."
        logger.warning(admin_warning)
        try:
            # Need a temporary root window for messagebox if pystray GUI hasn't started
            # This root window will be hidden immediately after the messagebox.
            root = tk.Tk()
            root.withdraw() # Hide the main Tkinter window
            messagebox.showwarning("Administrator Privileges Recommended", admin_warning)
            root.destroy() # Clean up the temporary root window
        except tk.TclError as e:
            logger.error(f"Failed to show Tkinter warning messagebox for admin rights (TclError: {e}). This can happen in environments without a display server or if Tkinter is not fully configured.", include_exception_info=True)
        except Exception as e:
            logger.error(f"Failed to show Tkinter warning messagebox for admin rights (Unknown Error: {e}).", include_exception_info=True)
    else:
        logger.info("Application running with administrator privileges.")
    
    _main_super_mode_manager = SuperModeManager()
    logger.info(f"SuperModeManager instantiated. Initial state: {'ON' if _main_super_mode_manager.is_active() else 'OFF'}")

    try:
        # Setup the global hotkey listener.
        # keyboard.add_hotkey will run the callback in a separate thread.
        keyboard.add_hotkey(SUPER_MODE_HOTKEY, on_hotkey_pressed)
        logger.info(f"Global hotkey '{SUPER_MODE_HOTKEY}' registered to toggle Super Mode.")
    except ImportError:
        logger.error("Failed to import 'keyboard' library. Hotkey functionality will be unavailable. Please install it: pip install keyboard", include_exception_info=True)
    except Exception as e:
        logger.error(f"Failed to register hotkey '{SUPER_MODE_HOTKEY}'. Error: {e}", include_exception_info=True)
        logger.warning("Hotkey functionality will be unavailable. This may be due to insufficient permissions (e.g., on Linux, run as root or configure user for uinput).")

    logger.info("Starting GUI...")
    # start_gui will block the main thread with pystray's run()
    # The core_manager_ref inside gui.py will be set by start_gui
    start_gui(_main_super_mode_manager) 

    # Cleanup hotkey when GUI exits (pystray run() finishes)
    try:
        logger.info("GUI finished. Unregistering hotkeys.")
        keyboard.unhook_all_hotkeys() # Or keyboard.remove_hotkey(SUPER_MODE_HOTKEY)
    except ImportError: # keyboard library might not have been imported successfully
        logger.warning("Keyboard library not available, skipping hotkey unregistration.")
    except Exception as e:
        logger.error(f"Error unregistering hotkeys: {e}", include_exception_info=True)

    logger.info("Application has finished GUI phase and is exiting.")

if __name__ == "__main__":
    # Note: On Linux, for global hotkeys, this script might need to be run as root
    # or your user needs to be in the 'input' group and have uinput permissions.
    main()
