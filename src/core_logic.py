# This file will contain the core business logic of the application.

import subprocess
import winreg # For later Windows-specific registry manipulations
import re # Add re for more robust parsing if not already imported
from src.config import DANGEROUS_APPS_PROCESS_NAMES, UPLOAD_LOGS, DEFAULT_FALLBACK_INTERFACES # Import DEFAULT_FALLBACK_INTERFACES
from src.logger import default_logger as logger

class SuperModeManager:
    """Manages the Super Mode state of the application, including network and USB control."""

    def __init__(self):
        """Initializes the SuperModeManager."""
        self._is_super_mode_active: bool = False
        self._disabled_interfaces: list[str] = []
        logger.info("SuperModeManager initialized.")

    def is_active(self) -> bool:
        """Returns True if Super Mode is active, False otherwise."""
        return self._is_super_mode_active

    def toggle_super_mode(self):
        """Toggles the Super Mode state and triggers corresponding actions."""
        self._is_super_mode_active = not self._is_super_mode_active
        if self._is_super_mode_active:
            logger.info("Super Mode Activated. Calling actions...")
            self._activate_actions()
        else:
            logger.info("Super Mode Deactivated. Calling actions...")
            self._deactivate_actions()

    def _activate_actions(self):
        """Actions to perform when Super Mode is activated."""
        logger.info("Core activation actions initiated.")
        self._control_network_adapters(enable=False)
        self._set_usb_storage_state(enable=False)
        self._clear_clipboard()
        self._manage_task_manager(disable=True)
        self._close_dangerous_apps()
        self._lock_screen()
        logger.info("Core activation actions completed.")

    def _deactivate_actions(self):
        """Actions to perform when Super Mode is deactivated."""
        logger.info("Core deactivation actions initiated.")
        self._control_network_adapters(enable=True)
        self._set_usb_storage_state(enable=True)
        self._manage_task_manager(disable=False)
        logger.info("Super Mode deactivation sequence complete.") # Adjusted log message
        
        if UPLOAD_LOGS:
            logger.info("Configuration enables log uploading. Attempting to upload logs now.")
            try:
                logger.upload_log() # Assumes 'logger' is the imported default_logger instance
            except Exception as e:
                # Catch any unexpected error from the upload_log call itself, though upload_log has its own extensive try-except
                logger.error(f"An unexpected error occurred when trying to initiate log upload: {e}", include_exception_info=True)
        else:
            logger.info("Log uploading is disabled in configuration. Skipping upload.")
        # logger.info("Core deactivation actions completed.") # This line is now covered by "Super Mode deactivation sequence complete."

    def _clear_clipboard(self):
        logger.info("Attempting to clear clipboard...")
        try:
            # Windows: cmd /c "echo off | clip"
            # This command effectively clears the clipboard by piping nothing into it.
            result = subprocess.run('cmd /c "echo off | clip"', shell=True, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                logger.info("Clipboard cleared successfully.")
            else:
                logger.error(f"Failed to clear clipboard. Return code: {result.returncode}. Error: {result.stderr}")
        except Exception as e:
            logger.error(f"Exception while trying to clear clipboard: {e}", include_exception_info=True)

    def _manage_task_manager(self, disable: bool):
        action_str = "disable" if disable else "enable"
        reg_path_policy = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
        value_name = "DisableTaskMgr"
        new_value_data = 1 if disable else 0 # 1 to disable, 0 to enable

        logger.info(f"Attempting to {action_str} Task Manager (requires admin rights and may need logout/gpupdate)...")
        try:
            # Connect to HKEY_CURRENT_USER as this is a user policy
            hkey_current_user = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            
            # Ensure the System key exists, create if not.
            key_policy_system = winreg.CreateKeyEx(hkey_current_user, reg_path_policy, 0, winreg.KEY_SET_VALUE)
            
            winreg.SetValueEx(key_policy_system, value_name, 0, winreg.REG_DWORD, new_value_data)
            
            winreg.CloseKey(key_policy_system)
            winreg.CloseKey(hkey_current_user)
            logger.info(f"Task Manager registry setting to '{action_str}' applied.")
            if disable:
                logger.info("Note: Task Manager disable might require a group policy update (gpupdate /force) or logout/login to take full effect.")
            else:
                logger.info("Note: Task Manager enable might require logout/login if it was previously disabled by policy.")

        except PermissionError:
            logger.warning(f"PermissionError: Could not {action_str} Task Manager. Administrator privileges may be required for some policy changes.")
        except OSError as e: # OSError can be due to various system issues including permissions
            logger.error(f"OSError: Could not {action_str} Task Manager. Error: {e}.", include_exception_info=True)
        except Exception as e:
            logger.error(f"An unexpected error occurred while trying to {action_str} Task Manager: {e}", include_exception_info=True)

    def _close_dangerous_apps(self):
        logger.info("Attempting to close dangerous applications...")
        if not DANGEROUS_APPS_PROCESS_NAMES:
            logger.info("No dangerous applications configured to close.")
            return

        closed_count = 0
        for app_name in DANGEROUS_APPS_PROCESS_NAMES:
            try:
                # Using /F for force, /IM for image name.
                # Add /T to kill child processes as well, if desired, but can be aggressive.
                command = ['taskkill', '/F', '/IM', app_name]
                logger.info(f"Attempting to kill process: {app_name}...")
                # Use shell=True on Windows if taskkill acts strangely without it, but better to avoid if possible.
                # For taskkill, not using shell=True is generally fine.
                result = subprocess.run(command, capture_output=True, text=True, check=False, encoding='cp437', errors='ignore')
                
                # taskkill success is often indicated by return code 0 AND specific stdout messages.
                # Error code 128 means "There are no running instances of the task." which is fine.
                # Error code 1 means "The operation attempted is not supported." (e.g. access denied)
                if result.returncode == 0:
                    logger.info(f"Successfully sent termination signal to {app_name}.")
                    closed_count +=1
                elif result.returncode == 128:
                    logger.info(f"Process {app_name} was not running.")
                elif "access is denied" in result.stderr.lower() or (result.returncode == 1 and "access is denied" in result.stderr.lower()): # More specific for RC 1 + access denied
                     logger.warning(f"Access denied trying to kill {app_name}. Closing specific applications via 'taskkill' may require administrator privileges.")
                elif result.returncode == 1: # General RC 1 if not clearly "access denied"
                     logger.warning(f"Operation to kill {app_name} may have failed (Return Code 1). StdErr: '{result.stderr.strip()}'. This can sometimes be due to insufficient privileges.")
                else:
                    # Some other error
                    logger.error(f"Failed to kill process {app_name}. Command: \"{' '.join(command)}\". Return code: {result.returncode}. stdout: '{result.stdout.strip()}', stderr: '{result.stderr.strip()}'")
            except FileNotFoundError:
                logger.error("Error: 'taskkill' command not found. Ensure it's in your system PATH.")
                # If taskkill is not found, we can't proceed with this method.
                return # Stop trying to close apps if taskkill isn't there
            except Exception as e:
                logger.error(f"Exception while trying to close {app_name}: {e}", include_exception_info=True)
        
        if closed_count > 0:
            logger.info(f"Successfully sent termination signals to {closed_count} listed application(s).")
        else:
            logger.info("No targeted dangerous applications were actively running or could be closed.")

    def _get_network_interfaces(self):
        '''
        Gets a list of enabled and connected network interface names.
        Uses 'netsh interface show interface' and parses the output.
        '''
        logger.info("Attempting to get network interfaces via netsh...")
        interface_names = []
        try:
            # Execute the netsh command
            # Using 'utf-8' or 'cp437' (common for console output) might be necessary
            # if default text decoding fails.
            result = subprocess.run(
                ['netsh', 'interface', 'show', 'interface'],
                capture_output=True, text=True, check=True, encoding='cp437', errors='ignore'
            )
            output = result.stdout

            # Example of parsing:
            # This parsing is basic and might need to be adjusted based on exact 'netsh' output format
            # on different Windows versions or locales.
            # It looks for lines that typically represent active physical interfaces.
            # Skips lines that are just headers or separators.
            # Assumes interface name is often at the end of relevant lines.
            lines = output.splitlines()
            for line in lines:
                line = line.strip()
                # Look for lines with state "Enabled" and type "Connected" (or similar keywords)
                # This is a heuristic and might need refinement.
                # Example line: "Enabled Connected Dedicated Wi-Fi"
                # Example line: "Enabled Connected Dedicated Ethernet"
                if line.startswith("Enabled") and "Connected" in line:
                    parts = line.split()
                    if len(parts) > 2: # Should have at least "Enabled", "Connected", "Type/Name"
                        # Heuristic: join parts from the 3rd element onwards as the name
                        # This handles names with spaces.
                        name_candidate = " ".join(parts[2:])
                        # Further filtering to avoid virtual adapters if possible (common names)
                        avoid_keywords = ["Loopback", "Bluetooth", "Virtual", "TAP", "RAS"]
                        if not any(avoid_keyword in name_candidate for avoid_keyword in avoid_keywords):
                            interface_names.append(name_candidate)
            
            if interface_names:
                logger.info(f"Found interfaces: {interface_names}")
            else:
                logger.warning("No suitable network interfaces found or parsed from netsh output.")
                logger.info(f"Falling back to configurable default interface list: {DEFAULT_FALLBACK_INTERFACES}.")
                return list(DEFAULT_FALLBACK_INTERFACES) # Return a copy

        except subprocess.CalledProcessError as e:
            logger.error(f"Error executing netsh to get interfaces: {e}", include_exception_info=True)
            logger.info(f"Falling back to configurable default interface list: {DEFAULT_FALLBACK_INTERFACES}.")
            return list(DEFAULT_FALLBACK_INTERFACES) # Return a copy
        except Exception as e:
            logger.error(f"An unexpected error occurred while getting network interfaces: {e}", include_exception_info=True)
            logger.info(f"Falling back to configurable default interface list: {DEFAULT_FALLBACK_INTERFACES}.")
            return list(DEFAULT_FALLBACK_INTERFACES) # Return a copy
            
        return interface_names

    def _control_network_adapters(self, enable: bool):
        action_cmd_str = 'enable' if enable else 'disable'
        interfaces_to_action = []

        if not enable:  # Disabling
            logger.info("Discovering active network interfaces to disable...")
            discovered_interfaces = self._get_network_interfaces() 
            
            # Check if the returned list IS the default fallback list.
            if discovered_interfaces == DEFAULT_FALLBACK_INTERFACES:
                logger.warning(f"_get_network_interfaces returned the configured fallback list: '{discovered_interfaces}'. Using this list for disabling.")
            # Even if it's the fallback, proceed to use it.
            # If discovered_interfaces is empty (e.g. if DEFAULT_FALLBACK_INTERFACES was empty), 
            # the existing "No network interfaces identified to disable" log will handle it.
            self._disabled_interfaces = discovered_interfaces
            
            interfaces_to_action = self._disabled_interfaces
            
            interfaces_to_action = self._disabled_interfaces
            
            if not interfaces_to_action: # Should not happen if fallback is ["Wi-Fi", "Ethernet"]
                logger.warning("No network interfaces identified to disable (empty list from discovery and fallback).")
                return
            logger.info(f"Interfaces targeted for {action_cmd_str}: {interfaces_to_action}")

        else:  # Enabling
            if not self._disabled_interfaces: # If no interfaces were disabled (e.g. SuperMode toggled off shortly after on, before disabling completed or if disabling failed)
                logger.info("No interfaces were specifically recorded as disabled by this session. Attempting to enable common interfaces from configured fallback.")
                interfaces_to_action = list(DEFAULT_FALLBACK_INTERFACES) # Use a copy of the fallback list for enabling
            else:
                interfaces_to_action = self._disabled_interfaces
            
            if not interfaces_to_action:
                logger.warning("No network interfaces identified to enable (empty stored list).")
                return
            logger.info(f"Interfaces targeted for {action_cmd_str}: {interfaces_to_action}")

        success_count = 0
        for if_name_str in interfaces_to_action:
            command = ['netsh', 'interface', 'set', 'interface', f'name={if_name_str}', f'admin={action_cmd_str}']
            try:
                logger.info(f"Executing: {' '.join(command)}")
                result = subprocess.run(command, capture_output=True, text=True, check=False, encoding='cp437', errors='ignore')
                
                output_lower = (result.stdout + result.stderr).lower()
                was_successful = True 
                
                if result.returncode != 0:
                    logger.info(f"Info: netsh command for '{if_name_str}' returned non-zero code: {result.returncode}")

                if "could not find the interface" in output_lower or "no such interface" in output_lower:
                    logger.warning(f"Interface '{if_name_str}' not found.")
                    was_successful = False
                elif "an interface with this name is not registered with the router" in output_lower:
                    logger.warning(f"Interface '{if_name_str}' not registered with the router.")
                    was_successful = False
                elif "the requested operation requires elevation" in output_lower:
                     logger.warning(f"Error for '{if_name_str}': The requested operation requires elevation (Run as administrator).")
                     was_successful = False
                elif result.returncode == 0 and not (result.stdout.strip() or result.stderr.strip()): # Command succeeded, no specific output
                    pass 
                elif result.returncode !=0 : 
                    logger.error(f"Failed to {action_cmd_str} interface '{if_name_str}'. Output: {(result.stdout + result.stderr).strip()}")
                    was_successful = False

                if was_successful:
                    logger.info(f"Successfully initiated {action_cmd_str} for interface: {if_name_str}")
                    success_count +=1
                else:
                    logger.warning(f"Attempt to {action_cmd_str} interface '{if_name_str}' may have failed or interface was not actionable.")

            except FileNotFoundError:
                logger.error("Error: 'netsh' command not found. Ensure it's in your system PATH.")
                return 
            except Exception as e:
                logger.error(f"An unexpected error occurred while trying to {action_cmd_str} interface '{if_name_str}': {e}", include_exception_info=True)
        
        if enable and success_count > 0 : 
             logger.info("Finished enabling attempt. Clearing stored disabled interfaces list.")
             self._disabled_interfaces = []
        elif enable and success_count == 0: # No interfaces enabled, keep the list for retry
             logger.warning(f"No interfaces were successfully enabled. Retaining the list: {self._disabled_interfaces} for next attempt if needed.")

    def _set_usb_storage_state(self, enable: bool):
        action_str = "enable" if enable else "disable"
        reg_path = r"SYSTEM\CurrentControlSet\Services\USBSTOR" # Backslashes explicitly escaped
        value_name = "Start"
        new_value_data = 3 if enable else 4

        logger.info(f"Attempting to {action_str} USB mass storage (requires admin rights)...")
        try:
            hkey_local_machine = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            # Ensure KEY_SET_VALUE is used for modifying the value.
            key_usbstor = winreg.OpenKey(hkey_local_machine, reg_path, 0, winreg.KEY_SET_VALUE) 
            winreg.SetValueEx(key_usbstor, value_name, 0, winreg.REG_DWORD, new_value_data)
            winreg.CloseKey(key_usbstor)
            winreg.CloseKey(hkey_local_machine)
            logger.info(f"USB mass storage devices have been {action_str}d successfully. (Registry modified)")
            logger.info("Note: A system reboot might be required for changes to take full effect.")
        except PermissionError:
            logger.warning(f"PermissionError: Could not {action_str} USB mass storage. Administrator privileges are required.")
        except FileNotFoundError:
            # This error occurs if the reg_path itself is not found.
            logger.error(f"FileNotFoundError: Registry path '{reg_path}' not found. The USBSTOR service may not be available on this system.")
        except OSError as e:
            # OSError can cover a range of issues, including some permission problems not caught by PermissionError,
            # or if the key is unexpectedly not available for modification.
            logger.error(f"OSError: Could not {action_str} USB mass storage. Error: {e}. This could be due to insufficient privileges or the key being protected.", include_exception_info=True)
        except Exception as e:
            logger.error(f"An unexpected error occurred while trying to {action_str} USB mass storage: {e}", include_exception_info=True)

    def _lock_screen(self):
        logger.info("Attempting to lock the screen...")
        try:
            # This command immediately locks the workstation on Windows.
            # It's equivalent to pressing Win+L.
            result = subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], check=False, capture_output=True, text=True)
            # This command usually doesn't produce stdout/stderr on success and might return quickly.
            # A specific return code check might not be very informative here,
            # but we check it anway. Typically, it should be 0 if the command was recognized.
            if result.returncode == 0:
                logger.info("Screen lock command executed successfully.")
            else:
                # This path might be taken if rundll32.exe or user32.dll has issues, which is rare.
                logger.warning(f"Screen lock command execution attempt finished. Return code: {result.returncode}. Stderr: '{result.stderr.strip()}'")

        except FileNotFoundError:
            # This would happen if rundll32.exe is not found, which is highly unlikely on a Windows system.
            logger.error("Error: 'rundll32.exe' command not found. Cannot lock screen.")
        except Exception as e:
            logger.error(f"An unexpected error occurred while trying to lock the screen: {e}", include_exception_info=True)

if __name__ == "__main__":
    # Note: When running this directly, the logger will use the default LOG_FILE_PATH from config.
    # Ensure src.config.LOG_FILE_PATH is set or it will use the logger's default.
    logger.info("SuperModeManager direct execution test started.")
    manager = SuperModeManager() # Logger is already active here from class init
    logger.info(f"Initial state: {manager.is_active()}")

    manager.toggle_super_mode() # Activate
    logger.info(f"State after first toggle: {manager.is_active()}")

    manager.toggle_super_mode() # Deactivate
    logger.info(f"State after second toggle: {manager.is_active()}")
    
    logger.info("SuperModeManager direct execution test finished. Check logs for details.")
    # The print below is for direct console feedback when running the file, separate from app logging.
    print("Reminder: Actual system actions are performed. Check application logs for detailed activity.")
