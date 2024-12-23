import platform
import sys
import os


class OSDetector:
    @staticmethod
    def get_os_info():
        """
        Returns detailed information about the operating system
        """
        os_info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "architecture": platform.architecture(),
            "platform": sys.platform,
            "os_name": os.name,
        }
        return os_info

    @staticmethod
    def is_windows():
        """Returns True if running on Windows"""
        return platform.system().lower() == "windows"

    @staticmethod
    def is_linux():
        """Returns True if running on Linux"""
        return platform.system().lower() == "linux"

    @staticmethod
    def get_os_type():
        """
        Returns the type of OS as a string
        """
        try:
            system = platform.system().lower()
            if system == "windows":
                return "windows"
            elif system == "linux":
                return "linux"
            elif system == "darwin":
                return "mac"
            else:
                return "unknown"
        except Exception as e:
            print(f"Error detecting OS: {str(e)}")
            return "error"

    @staticmethod
    def get_path_separator():
        """Returns the appropriate path separator for the current OS"""
        return "\\" if OSDetector.is_windows() else "/"


if __name__ == "__main__":
    # Usage example:
    # Get basic OS type
    os_type = OSDetector.get_os_type()
    print(f"OS Type: {os_type}")

    # Check if Windows
    if OSDetector.is_windows():
        print("Running on Windows")

    # Check if Linux
    if OSDetector.is_linux():
        print("Running on Linux")

    # Get path separator
    separator = OSDetector.get_path_separator()
    print(f"Path separator: {separator}")

    # Get detailed OS info
    os_info = OSDetector.get_os_info()
    print("\nDetailed OS Information:")
    for key, value in os_info.items():
        print(f"{key}: {value}")

    # Example of using path separator
    def create_path(base_path, file_name):
        separator = OSDetector.get_path_separator()
        return f"{base_path}{separator}{file_name}"

    # Example path
    path = create_path("folder", "file.txt")
    print(f"\nCreated path: {path}")
