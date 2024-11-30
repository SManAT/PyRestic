import os
import sys
import shutil


class TerminalColors:
    """Class to set terminal background and print colored text"""

    class Default:
        DEFAULT = (200, 200, 200)
        RED = (255, 0, 0)
        YELLOW = (244, 221, 33)
        CYAN = (42, 161, 152)
        BACKGROUND = (0, 0, 0)

    class Solarized:
        DEFAULT = (38, 139, 210)
        RED = (220, 50, 47)
        YELLOW = (181, 137, 0)
        CYAN = (42, 161, 152)
        BACKGROUND = (253, 246, 227)

    def __init__(self, theme="Default"):
        # Enable ANSI escape sequences in Windows
        # Enable ANSI escape sequences in Windows
        if os.name == "nt":
            import ctypes

            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        os.system("")

        self.theme = getattr(self, theme)
        self.current_bg = None
        self.default_fg = getattr(self.theme, "DEFAULT")  # Store default foreground color

    def _validate_rgb(self, r: int, g: int, b: int) -> None:
        """Validate RGB values are within range"""
        for value in (r, g, b):
            if not 0 <= value <= 255:
                raise ValueError(f"RGB values must be between 0 and 255, got {value}")

    def _get_fg_color(self, r: int, g: int, b: int) -> str:
        """Get ANSI escape sequence for foreground color"""
        return f"\033[38;2;{r};{g};{b}m"

    def _get_bg_color(self, r: int, g: int, b: int) -> str:
        """Get ANSI escape sequence for background color"""
        return f"\033[48;2;{r};{g};{b}m"

    def set_background(self, r: int, g: int, b: int) -> None:
        """Set terminal background to specified RGB color"""
        self._validate_rgb(r, g, b)
        self.current_bg = (r, g, b)

        # Create escape sequences
        bg_color = self._get_bg_color(r, g, b)
        fg_color = self._get_fg_color(*self.default_fg)  # Default foreground color

        # Combined color sequence
        color_sequence = f"{bg_color}{fg_color}"

        # Clear screen first
        os.system("cls" if os.name == "nt" else "clear")

        # Set colors
        sys.stdout.write(color_sequence)

        # Fill entire screen
        columns, rows = shutil.get_terminal_size()
        for _ in range(rows + 1):
            sys.stdout.write(color_sequence + " " * columns + "\n")

        # Reset cursor position but keep colors
        sys.stdout.write("\033[H")
        sys.stdout.write(color_sequence)
        sys.stdout.flush()

        # Set colors for standard output and error
        sys.__stdout__.write(color_sequence)
        sys.__stderr__.write(color_sequence)
        sys.stderr.write(color_sequence)

        # For Windows, set these colors as default
        if os.name == "nt":
            os.system(f"echo \033[38;2;{self.default_fg[0]};{self.default_fg[1]};{self.default_fg[2]}m")

    def set_BackgroundColor(self, color_name: str = "BACKGROUND"):
        """Set background using Theme color scheme"""
        try:
            color = getattr(self.theme, color_name.upper())
            self.set_background(*color)
        except AttributeError:
            valid_colors = [attr for attr in dir(self.theme) if not attr.startswith("__")]
            raise ValueError(f"Invalid color name. Choose from: {', '.join(valid_colors)}")

    def print_colored(self, text: str, r: int, g: int, b: int) -> None:
        """Print text in specified RGB color"""
        bg_part = self._get_bg_color(*self.current_bg) if self.current_bg else ""
        colored_text = f"{bg_part}{self._get_fg_color(r, g, b)}{text}"
        if self.current_bg:
            # Reset to default foreground color but keep background
            colored_text += f"{self._get_fg_color(*self.default_fg)}"
        print(colored_text)

    def print(self, text: str, color_name: str = "DEFAULT"):
        """Print text using Theme color scheme"""
        try:
            color = getattr(self.theme, color_name.upper())
            self.print_colored(text, *color)
        except AttributeError:
            valid_colors = [attr for attr in dir(self.theme) if not attr.startswith("__")]
            raise ValueError(f"Invalid color name. Choose from: {', '.join(valid_colors)}")

    def reset(self) -> None:
        """Reset terminal colors to default"""
        self.current_bg = None
        sys.stdout.write("\033[0m")
        os.system("cls" if os.name == "nt" else "clear")
        sys.stdout.flush()

    def Linebreak(self):
      self.print("\n")


# Example usage with error handling to test traceback colors
if __name__ == "__main__":
    colors = TerminalColors()

    # Set background
    colors.set_BackgroundColor("BACKGROUND")

    # Print some colored text
    colors.print("This is default blue")
    colors.print("This is red", "RED")
    colors.print("This is yellow", "YELLOW")
    colors.print("This is cyan", "CYAN")

    # Test error handling to see traceback colors
    try:
        1 / 0
    except Exception as e:
        colors.print(f"Error occurred: {e}", "RED")
