import subprocess
import threading
import sys
import time
from typing import Callable, List


class CmdRunner:
    SHOW_PROGRESS = True
    NO_PROGRESS = False

    REALTIME_OUTPUT = True
    NO_REALTIME_OUTPUT = False

    def __init__(self):
        self._stderr = ""
        self._stdout = ""
        self.pid = None
        self._thread = None
        self._finished = threading.Event()
        self._spinner = None
        self.spinnerText = None

        self._suppress_realtime = False  # flag for suppressing realtime output
        self._buffered_output = []  # Buffer to store output when suppressed

        # Event system
        self._stdout_listeners: List[Callable[[str], None]] = []
        self._stderr_listeners: List[Callable[[str], None]] = []
        self._completion_listeners: List[Callable[[], None]] = []

    def set_spinner_text(self, txt):
        """Sets the Text in Front of the spinner"""
        self.spinnerText = txt

    def getStdErr(self):
        return self._stderr

    def getStdOut(self):
        return self._stdout

    def set_suppress_realtime(self, suppress: bool):
        """Set whether to suppress realtime output"""
        self._suppress_realtime = suppress

    def add_stdout_listener(self, callback: Callable[[str], None]) -> None:
        """Add a listener for stdout updates"""
        self._stdout_listeners.append(callback)

    def add_stderr_listener(self, callback: Callable[[str], None]) -> None:
        """Add a listener for stderr updates"""
        self._stderr_listeners.append(callback)

    def add_completion_listener(self, callback: Callable[[], None]) -> None:
        """Add a listener for command completion"""
        self._completion_listeners.append(callback)

    def remove_stdout_listener(self, callback: Callable[[str], None]):
        """Remove a stdout listener"""
        if callback in self._stdout_listeners:
            self._stdout_listeners.remove(callback)

    def remove_stderr_listener(self, callback: Callable[[str], None]):
        """Remove a stderr listener"""
        if callback in self._stderr_listeners:
            self._stderr_listeners.remove(callback)

    def remove_completion_listener(self, callback: Callable[[], None]):
        """Remove a completion listener"""
        if callback in self._completion_listeners:
            self._completion_listeners.remove(callback)

    def _notify_stdout(self, line: str) -> None:
        """Notify all stdout listeners"""
        if self._suppress_realtime:
            self._buffered_output.append(line)
        else:
            for listener in self._stdout_listeners:
                try:
                    listener(line)
                except Exception as e:
                    print(f"Error in stdout listener: {e}")

    def _notify_stderr(self, line: str):
        """Notify all stderr listeners"""
        if self._suppress_realtime:
            self._buffered_output.append(line)
        else:
            for listener in self._stderr_listeners:
                try:
                    listener(line)
                except Exception as e:
                    print(f"Error in stderr listener: {e}")

    def _notify_completion(self):
        """Notify all completion listeners"""
        if self._suppress_realtime is False:
            for listener in self._completion_listeners:
                try:
                    listener()
                except Exception as e:
                    print(f"Error in completion listener: {e}")

    def _run_with_progress(self, info_text):
        """
        Show working state
        :param info_text: Text to be displayed in front of animation
        """
        chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        i = 0
        while not self._finished.is_set():
            sys.stdout.write(f"\r{info_text} {chars[i % len(chars)]}")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
        sys.stdout.write("\n")
        sys.stdout.flush()

        # Print buffered output after spinner
        if self._suppress_realtime:
            for line in self._buffered_output:
                print(line.strip())
            self._buffered_output.clear()

    def _execute_command(self, cmd, is_ps=False):
        self._stderr = ""
        self._stdout = ""

        if is_ps:
            proc = subprocess.Popen(["powershell.exe", cmd], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0, preexec_fn=None)
        else:
            proc = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0, preexec_fn=None)

        self.pid = proc.pid

        def read_stderr():
            for line in iter(proc.stderr.readline, b""):
                decoded_line = line.decode("utf-8", "ignore")
                self._stderr += decoded_line
                self._notify_stderr(decoded_line)

        def read_stdout():
            for line in iter(proc.stdout.readline, b""):
                decoded_line = line.decode("utf-8", "ignore")
                self._stdout += decoded_line
                self._notify_stdout(decoded_line)

        # Create and start threads for reading stdout and stderr
        stderr_thread = threading.Thread(target=read_stderr)
        stdout_thread = threading.Thread(target=read_stdout)

        stderr_thread.start()
        stdout_thread.start()

        stderr_thread.join()
        stdout_thread.join()

        proc.communicate()
        self._finished.set()
        self._notify_completion()

    def runCmd_Silent(self, cmd):
        """Run command no Output"""
        self.runCmd(cmd, self.NO_REALTIME_OUTPUT, self.NO_PROGRESS)

    def runCmd_with_Spinner(self, cmd, text):
        """Run command with spinner and text in front"""
        self.set_spinner_text(text)
        self.runCmd(cmd, self.NO_REALTIME_OUTPUT, self.SHOW_PROGRESS)

    def runCmdInShell(self, thecmd):
        """run thecomd in extra shell"""
        subprocess.Popen("wt.exe {thecmd}", shell=True)

    def runCmd(self, cmd, realtime_output=REALTIME_OUTPUT, progress_mode=NO_PROGRESS):
        """
        Runs a command in a thread, schows realtime output and no progress spinner
        :param cmd: Command to run
        :param info: Text to be display in front
        :param show_progress: Whether to show a progress indicator
        :param suppress_realtime: Whether to suppress realtime output
        :return: None
        """
        if self.spinnerText is None:
            self.set_spinner_text("Running command ")

        self._finished.clear()
        self._buffered_output.clear()
        self.set_suppress_realtime(not realtime_output)  # invert!

        self._thread = threading.Thread(target=self._execute_command, args=(cmd, False))
        self._thread.start()

        if progress_mode:
            progress_thread = threading.Thread(target=self._run_with_progress, args=(self.spinnerText,))
            progress_thread.start()

        # Wait for completion
        self._thread.join()
        if progress_mode:
            progress_thread.join()

    def runPSFile(self, filename, realtime_output=REALTIME_OUTPUT, progress_mode=NO_PROGRESS):
        """
        Runs a PowerShell file in a thread
        :param filename: PowerShell file to run
        :param info: Text to be display in front
        :param show_progress: Whether to show a progress indicator
        :param suppress_realtime: Whether to suppress realtime output
        :return: None
        """
        if self.spinnerText is None:
            self.set_spinner_text("Running command ")

        self._finished.clear()
        self._buffered_output.clear()
        self.set_suppress_realtime(not realtime_output)  # invert!

        self._thread = threading.Thread(target=self._execute_command, args=(filename, self.spinnerText, True))
        self._thread.start()

        if progress_mode:
            progress_thread = threading.Thread(target=self._run_with_progress, args=(self.spinnerText,))
            progress_thread.start()

        # Wait for completion
        self._thread.join()
        if progress_mode:
            progress_thread.join()


# Example usage:
if __name__ == "__main__":

    def on_stdout(line):
        print(f"STDOUT Update: {line.strip()}")

    def on_stderr(line):
        print(f"STDERR Update: {line.strip()}")

    def on_completion():
        print("Command completed!")

    runner = CmdRunner()

    # Add listeners
    runner.add_stdout_listener(on_stdout)
    runner.add_stderr_listener(on_stderr)
    runner.add_completion_listener(on_completion)

    # Run a command with progress indicator
    runner.runCmd("ping google.com")

    # Run another command without progress indicator
    # runner.runCmd("dir", show_progress=False)

    # Example with real-time processing
    def process_output(line):
        # Process each line as it comes
        if "bytes=" in line:
            print(f"Ping response received: {line.strip()}")

    runner = CmdRunner()
    runner.add_stdout_listener(process_output)
    runner.runCmd("ping -n 4 google.com")
