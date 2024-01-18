from datetime import datetime
from pathlib import Path
from typing import Optional


class Logger:
    def __init__(self, log_file: Optional[Path] = None, mute_stdout: bool = False):
        """
        The Logger class represents a simple class for logging output to standard out and/or an output file.

        :param log_file: An optional path to a log file to report messages
        :param mute_stdout: A True/False flag for whether to mute standard output or not, by default std out is on.
        """
        self._file = log_file
        if self._file:
            self._file.write_text("")
        self._print_to_stdout = not mute_stdout

    def log(self, message: str) -> None:
        """
        Emit a message to the log locations, such as standard output or the specified log file.

        :param message: The message to emit, which is formatted along with a timestamp
        :return: None
        """
        message = f"{datetime.now()} : {message}"
        if self._print_to_stdout:
            print(message)
        if self._file:
            with self._file.open(mode='a') as file:
                file.write(message)

    @staticmethod
    def terminal_progress_bar(current_num: int, total_num: int, suffix: str) -> None:
        """
        A static log function that can be called to specifically emit a progress indicator to standard output.
        Note that this function intentionally does not write a new line character so that the progress bar
        can show up dynamically on the terminal.  Once the progress is complete, either call terminal_progress_done, or
        print an empty string to the terminal before sending more messages.

        :param current_num: The current progress count
        :param total_num: The maximum progress count
        :param suffix: A string suffix to show after the progress bar
        :return: None
        """
        percent_done = round(100 * (current_num / total_num), 3)
        filled_length = int(80 * (percent_done / 100.0))
        bar = "*" * filled_length + '-' * (80 - filled_length)
        print(f"\r                  Progress : |{bar}| {percent_done}% - {suffix}", end='')

    @staticmethod
    def terminal_progress_done() -> None:
        """
        A static log function that nicely finishes a progress bar that was created/updated using the
        terminal_progress_bar function.  This function will set the progress bar to 100%
        :return: None
        """
        Logger.terminal_progress_bar(1, 1, 'Finished\n')


logger = Logger()  # create a default instance to help with logging, use a custom instance if desired
