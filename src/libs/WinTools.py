import os
import winshell
from win32com.client import Dispatch


class WinTools:
    """
    create Shortcuts in Windows
    desktop = winshell.desktop()
    start_menu = winshell.start_menu()
    programs = winshell.programs()
    startup = winshell.startup()
    """

    def __init__(self):
        pass

    def create_advanced_shortcut(self, target_path, shortcut_path, description="", icon_path="", working_dir="", arguments="", hotkey=""):
        """
        Create a Windows shortcut with advanced options

        Args:
            target_path (str): Path to the target executable or file
            shortcut_path (str): Path where to create the shortcut
            description (str): Description of the shortcut
            icon_path (str): Path to icon file
            working_dir (str): Working directory for the shortcut
            arguments (str): Command line arguments
            hotkey (str): Hotkey combination (e.g., "CTRL+ALT+P")
        """
        try:
            shell = Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)

            # Set basic properties
            shortcut.Targetpath = target_path
            shortcut.Description = description

            # Set optional properties
            if icon_path:
                shortcut.IconLocation = icon_path
            if working_dir:
                shortcut.WorkingDirectory = working_dir
            if arguments:
                shortcut.Arguments = arguments
            if hotkey:
                shortcut.Hotkey = hotkey

            # Save the shortcut
            shortcut.save()
            print(f"Shortcut created successfully: {shortcut_path}")
            return True

        except Exception as e:
            print(f"Error creating shortcut: {str(e)}")
            return False

    def create_shortcut(self, target_path, shortcut_path, description="", icon_path=""):
        """
        Create a Windows shortcut (.lnk file)

        Args:
            target_path (str): Path to the target executable or file
            shortcut_path (str): Path where to create the shortcut
            description (str): Description of the shortcut
            icon_path (str): Path to icon file (optional)
        """
        try:
            shell = Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target_path
            shortcut.Description = description
            if icon_path:
                shortcut.IconLocation = icon_path
            shortcut.save()
            print(f"Shortcut created successfully: {shortcut_path}")
            return True
        except Exception as e:
            print(f"Error creating shortcut: {str(e)}")
            return False


# Example usage
if __name__ == "__main__":
    wintools = WinTools()

    # Basic shortcut creation
    target = r"C:\Windows\notepad.exe"
    shortcut = os.path.join(winshell.desktop(), "Notepad.lnk")
    wintools.create_shortcut(target, shortcut, "Notepad Shortcut")

    # Advanced shortcut creation
    # wintools.create_advanced_shortcut(
    #    target_path=r"C:\Windows\notepad.exe",
    #    shortcut_path=os.path.join(winshell.desktop(), "Notepad Advanced.lnk"),
    #    description="Notepad with custom settings",
    #    icon_path=r"C:\Windows\notepad.exe",
    #    working_dir=r"C:\Users\Documents",
    #    arguments="example.txt",
    #    hotkey="CTRL+ALT+N",
    # )

    # Create shortcut in Start Menu
    # start_menu = winshell.start_menu()
    # shortcut_path = os.path.join(start_menu, "My Program.lnk")
    # wintools.create_shortcut(target_path=r"C:\Program Files\MyProgram\program.exe", shortcut_path=shortcut_path)

    # Create shortcut with arguments
    # wintools.create_advanced_shortcut(
    #    target_path=r"C:\Program Files\MyProgram\program.exe", shortcut_path=r"C:\Users\Username\Desktop\MyProgram.lnk", arguments="--config config.ini", working_dir=r"C:\Program Files\MyProgram"
    # )
