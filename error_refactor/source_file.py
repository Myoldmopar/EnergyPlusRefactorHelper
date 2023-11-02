from pathlib import Path
from typing import List


class SourceFile:
    def __init__(self, path: Path):
        self.path = path
        self.identified_error_blocks = self.process()

    def process(self) -> List[int]:
        # need to track where the error messages start, end, etc.
        # find the first instance of ShowFatal or whatever, and follow it to the next same-level semicolon?
        return [len(str(self.path)), 1, 0]
