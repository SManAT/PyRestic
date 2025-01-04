import subprocess
import os
from typing import Optional, Union, List, Callable

""" Runs a command in Terminal, and blocks until the command has finished """


class CmdRunner_Terminal:
    def __init__(self, working_directory: Optional[str] = None):
        """Initialize command runner.
        :param working_directory: Path to working directory, uses current if None"""
        self.working_directory = working_directory or os.getcwd()
        self.process = None
        self.on_complete_callback: Optional[Callable] = None

    def set_complete_callback(self, callback: Callable[[int], None]):
        """Set callback for process completion.
        :param callback: Function to call when process completes, receives return code"""
        self.on_complete_callback = callback

    def run_command(self, command: Union[str, List[str]], timeout: Optional[float] = None) -> None:
        """Run command and block until completion.
        :param command: Command to run (string or list)
        :param timeout: Maximum time to wait for completion in seconds"""
        if isinstance(command, list):
            command = " ".join(command)

        try:
            # This will block until the process completes
            completed_process = subprocess.run(command, shell=True, cwd=self.working_directory, check=True, text=True)  # This will raise an exception if the command fails

            if self.on_complete_callback:
                self.on_complete_callback(completed_process.returncode)

        except subprocess.CalledProcessError as e:
            print(f"Command failed with return code {e.returncode}")
            if self.on_complete_callback:
                self.on_complete_callback(e.returncode)
            raise
        except Exception as e:
            print(f"Failed to execute command: {e}")
            raise

    def close(self):
        """Cleanup method (kept for compatibility)"""
        pass


if __name__ == "__main__":
    # Your usage:
    cmd = "your command here"
    runner = CmdRunner_Terminal()
    # This will block until completion
    runner.run_command(cmd)
