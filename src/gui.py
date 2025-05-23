# src/gui.py

import sys # For exiting
from PIL import Image, ImageDraw # For creating a simple icon. Pillow is a pystray dependency.
from pystray import Icon as PystrayIcon, Menu as PystrayMenu, MenuItem as PystrayMenuItem

# Assuming SuperModeManager and logger are passed or imported
# For this example, we'll rely on them being passed to start_gui.
# from src.logger import default_logger as logger # Already in main.py, GUI can use passed manager's logger if needed or its own
# from src.core_logic import SuperModeManager # Passed to start_gui

# Global reference to the icon and core_manager to be accessible by menu actions
# This is a common pattern for pystray menu callbacks.
tray_icon = None
core_manager_ref = None 
# logger_ref = None # If GUI needs to log directly

def create_placeholder_image(width=64, height=64, color1='red', color2='blue', is_on=False):
    """Creates a simple PIL Image for the tray icon."""
    image = Image.new('RGB', (width, height), color1 if not is_on else color2)
    dc = ImageDraw.Draw(image)
    # Simple design: a filled circle or different color based on state
    if is_on:
        dc.ellipse([(width // 4, height // 4), (width * 3 // 4, height * 3 // 4)], fill=color1)
    else:
        dc.ellipse([(width // 4, height // 4), (width * 3 // 4, height * 3 // 4)], fill=color2)
    return image

def update_icon_status():
    """Updates the icon's appearance or tooltip based on Super Mode status."""
    global tray_icon, core_manager_ref
    if tray_icon and core_manager_ref:
        is_on = core_manager_ref.is_active()
        tray_icon.icon = create_placeholder_image(is_on=is_on)
        tray_icon.title = f"Super Mode ({'ON' if is_on else 'OFF'})" 
        # logger_ref.info(f"GUI: Icon status updated. Super Mode is {'ON' if is_on else 'OFF'}.")


def on_toggle_super_mode_clicked(icon, item):
    """Callback when 'Toggle Super Mode' is clicked."""
    global core_manager_ref #, logger_ref
    if core_manager_ref:
        # logger_ref.info("GUI: 'Toggle Super Mode' clicked.")
        print("GUI: 'Toggle Super Mode' clicked.") # Use print for now, will be logged by core_manager
        core_manager_ref.toggle_super_mode() # This will trigger logging inside core_logic
        update_icon_status() # Update icon based on new state

def on_exit_clicked(icon, item):
    """Callback when 'Exit' is clicked."""
    global tray_icon #, logger_ref
    # logger_ref.info("GUI: 'Exit' clicked. Shutting down application.")
    print("GUI: 'Exit' clicked. Shutting down application.")
    if tray_icon:
        tray_icon.stop()
    # sys.exit(0) # This might be too abrupt, pystray's stop() should allow main thread to finish

def start_gui(manager): # manager is the SuperModeManager instance
    """Initializes and runs the system tray GUI."""
    global tray_icon, core_manager_ref #, logger_ref
    core_manager_ref = manager
    # logger_ref = logger # If you pass logger from main.py or import default_logger

    # logger_ref.info("GUI: Initializing system tray icon...")
    print("GUI: Initializing system tray icon...")


    # Initial icon state
    initial_icon_image = create_placeholder_image(is_on=core_manager_ref.is_active())
    initial_title = f"Super Mode ({'ON' if core_manager_ref.is_active() else 'OFF'})"

    # Define the menu
    menu = PystrayMenu(
        PystrayMenuItem('Toggle Super Mode', on_toggle_super_mode_clicked),
        PystrayMenuItem('Exit', on_exit_clicked)
    )

    # Create and run the icon
    tray_icon = PystrayIcon(
        "SuperModeApp", 
        icon=initial_icon_image, 
        title=initial_title, 
        menu=menu
    )
    
    # logger_ref.info("GUI: Running system tray icon. Application is now in background.")
    print("GUI: Running system tray icon. Application is now in background.")
    # The run() method is blocking and will keep the application alive.
    # It needs to be run in the main thread.
    tray_icon.run() 
    # After tray_icon.stop() is called (e.g. by on_exit_clicked), execution continues here.
    print("GUI: Pystray icon run loop finished.")


if __name__ == '__main__':
    # This allows testing gui.py directly if needed.
    print("GUI: Running gui.py directly (for testing system tray).")
    
    # Mock SuperModeManager for direct testing
    class MockSuperModeManager:
        def __init__(self):
            self._is_active = False
            print("MockSuperModeManager initialized for GUI test.")
        def is_active(self):
            return self._is_active
        def toggle_super_mode(self):
            self._is_active = not self._is_active
            print(f"MockSuperModeManager: Super Mode toggled to {'ON' if self._is_active else 'OFF'}")
            # In a real scenario, this would also trigger logging via the actual logger.

    mock_manager = MockSuperModeManager()
    # mock_logger = ... # if you want to test logging from GUI directly
    start_gui(mock_manager) # Pass mock manager
    print("GUI: Direct test of gui.py finished.")
