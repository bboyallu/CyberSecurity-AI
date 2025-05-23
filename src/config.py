# Configuration for the CyberSecurity AI Tool

# List of process executable names considered "dangerous"
# These will be targeted for termination when Super Mode activates.
# Add or remove process names as needed.
DANGEROUS_APPS_PROCESS_NAMES = [
    "chrome.exe",
    "firefox.exe",
    "msedge.exe",
    "opera.exe",
    "brave.exe",
    "iexplore.exe", # Internet Explorer
    # File transfer / sync
    "dropbox.exe",
    "onedrive.exe",
    "googledrivesync.exe",
    # Torrent clients
    "utorrent.exe",
    "qbittorrent.exe",
    "transmission-qt.exe",
    # Common communication apps that might be distracting or insecure
    "slack.exe",
    "discord.exe",
    "skype.exe",
    "telegram.exe",
    # Remote desktop
    "mstsc.exe", # Microsoft Remote Desktop
    "anydesk.exe",
    "teamviewer.exe",
]

# Hotkey configuration (placeholder for now)
SUPER_MODE_HOTKEY = "Ctrl+Alt+Shift+S"

# Logging configuration (placeholders for now)
LOG_FILE_PATH = "super_mode_log.txt" # Or whatever it is currently
UPLOAD_LOGS = True # Set to True to enable log uploading by default for now
LOG_UPLOAD_URL = "https://your-log-server.com/api/upload_log" # Placeholder URL
LOG_UPLOAD_EMAIL = "" # Not used for web server upload

# Default list of network interfaces to use as a fallback if dynamic detection fails.
# These names are common, but might not match all systems.
DEFAULT_FALLBACK_INTERFACES = ["Wi-Fi", "Ethernet"]

if __name__ == '__main__':
    # Example of accessing configuration
    print("Dangerous Application Executables:")
    for app_name in DANGEROUS_APPS_PROCESS_NAMES:
        print(f"- {app_name}")
    print(f"Configured Hotkey: {SUPER_MODE_HOTKEY}")
