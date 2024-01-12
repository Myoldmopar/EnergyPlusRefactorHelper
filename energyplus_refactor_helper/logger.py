from datetime import datetime
from pathlib import Path
from typing import Optional


class Logger:
    def __init__(self, log_file: Optional[Path] = None, mute_stdout: bool = False):
        self._file = log_file
        if self._file:
            self._file.write_text("")
        self._print_to_stdout = not mute_stdout

    def log(self, message: str):
        message = f"{datetime.now()} : {message}"
        if self._print_to_stdout:
            print(message)
        if self._file:
            with self._file.open(mode='a') as file:
                file.write(message)

    @staticmethod
    def terminal_progress_bar(current_num: int, total_num: int, suffix: str):
        percent_done = round(100 * (current_num / total_num), 3)
        filled_length = int(80 * (percent_done / 100.0))
        bar = "*" * filled_length + '-' * (80 - filled_length)
        print(f"\r                  Progress : |{bar}| {percent_done}% - {suffix}", end='')


logger = Logger()  # create a default instance to help with logging
