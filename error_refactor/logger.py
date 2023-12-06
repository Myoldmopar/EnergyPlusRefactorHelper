from datetime import datetime
from pathlib import Path
from typing import Optional


class Logger:
    def __init__(self, log_file: Optional[Path] = None, mute_stdout: bool = False):
        self._file = log_file
        if self._file:
            self._file.unlink()
        self._print_to_stdout = not mute_stdout

    def log(self, message: str):
        message = f"{datetime.now()} : {message}"
        if self._print_to_stdout:
            print(message)
        if self._file:
            with self._file.open(mode='a') as file:
                file.write(message)


# create a default instance that just prints to stdout
logger = Logger()
