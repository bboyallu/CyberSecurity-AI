import datetime
import os
import requests # For log uploading
from src.config import LOG_FILE_PATH, UPLOAD_LOGS, LOG_UPLOAD_URL 

class Logger:
    def __init__(self, log_file_path=None):
        self.log_file = log_file_path if log_file_path else LOG_FILE_PATH
        # Ensure log directory exists (if any specified in path)
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
                print(f"Log directory created: {log_dir}")
            except OSError as e:
                print(f"Error creating log directory {log_dir}: {e}. Logging to current directory.")
                # Fallback to current directory if subdir creation fails
                self.log_file = os.path.basename(self.log_file) 
        
        self._initialize_log_file()

    def _initialize_log_file(self):
        # You might want to add a log rotation mechanism here in a more advanced version
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"--- Log started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        print(f"Logger initialized. Logging to: {self.log_file}")

    def log(self, message, level="INFO"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}\n"
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(formatted_message)
        except Exception as e:
            # Fallback to print if file logging fails
            print(f"Error writing to log file {self.log_file}: {e}")
            print(formatted_message)

    # Convenience methods for different levels
    def info(self, message):
        self.log(message, level="INFO")

    def warning(self, message):
        self.log(message, level="WARNING")

    def error(self, message, include_exception_info=False):
        if include_exception_info:
            import traceback
            exc_info = traceback.format_exc()
            self.log(f"{message}\nException Info:\n{exc_info}", level="ERROR")
        else:
            self.log(message, level="ERROR")

    def upload_log(self):
        if not UPLOAD_LOGS:
            # self.info("Log uploading is disabled in config.") # Avoid logging about not logging during upload
            print("Logger: Log uploading is disabled in config.") # Use print if self.info could trigger upload
            return

        if not LOG_UPLOAD_URL:
            self.error("Log uploading is enabled, but LOG_UPLOAD_URL is not configured.")
            return

        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            if not log_content.strip():
                self.info("Log file is empty. Nothing to upload.")
                return

            # Basic headers; you might want to add content-type or auth tokens in a real app
            headers = {
                'User-Agent': 'SuperModeApp/1.0'
            }
            
            # You could send as plain text, form data, or JSON.
            # Sending as plain text in the body for this example.
            # For JSON: data = {'log_data': log_content}, then use requests.post(..., json=data)
            
            self.info(f"Attempting to upload log to {LOG_UPLOAD_URL}...")
            response = requests.post(LOG_UPLOAD_URL, data=log_content, headers=headers, timeout=15) # 15s timeout

            if response.status_code == 200 or response.status_code == 201: # Common success codes
                self.info(f"Log uploaded successfully to {LOG_UPLOAD_URL}. Status: {response.status_code}")
                # Optional: Clear or archive the log file after successful upload
                # For now, we'll leave it.
                # with open(self.log_file, 'w', encoding='utf-8') as f:
                #     f.write(f"--- Log uploaded at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} and cleared ---\n")
            else:
                self.error(f"Failed to upload log. Server responded with status {response.status_code}. Response: {response.text[:200]}") # Log first 200 chars of response

        except FileNotFoundError:
            self.error(f"Log file {self.log_file} not found for upload.")
        except requests.exceptions.RequestException as e:
            self.error(f"Error during log upload request to {LOG_UPLOAD_URL}: {e}", include_exception_info=True)
        except Exception as e:
            self.error(f"An unexpected error occurred during log upload: {e}", include_exception_info=True)

# Global logger instance (optional, but can be convenient)
# Usage: from src.logger import default_logger
# default_logger.info("This is a test message.")
default_logger = Logger()

if __name__ == '__main__':
    # Example Usage:
    # Create a logger instance (or use default_logger)
    logger = Logger("test_app_log.txt") # Override default path for testing
    logger.info("Application started.")
    logger.warning("This is a test warning.")
    
    try:
        x = 1 / 0
    except ZeroDivisionError:
        logger.error("A division by zero occurred!", include_exception_info=True)
    
    logger.info("Application finished.")
    print(f"Test log written to {logger.log_file}")

    # Test default logger
    default_logger.info("Default logger test: App starting up.")
    default_logger.error("Default logger test: Something went wrong.")

    # Testing log upload (requires a listening server at the configured URL):
    print("\nTesting log upload (requires a listening server at the configured URL or will fail):")
    if UPLOAD_LOGS and LOG_UPLOAD_URL:
        # default_logger.info("This is a pre-upload log message for default_logger.")
        # default_logger.upload_log() # Test with default logger
        logger.info("This is a pre-upload log message for 'test_app_log.txt'.") # Assuming logger instance from earlier example
        logger.upload_log() # Test with specific logger instance
    else:
        print("Log uploading is not enabled or URL not configured, skipping upload test.")
