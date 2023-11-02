from pathlib import Path
from typing import List

#  from error_refactor.source_file import SourceFile


class SourceFolder:
    def __init__(self, root_path: Path):
        self.root = root_path
        self.matched_files = self.locate_source_files()

    def locate_source_files(self) -> List[Path]:
        known_patterns = ["*.cc", "*.hh", "*.cpp"]
        all_files = []
        for pattern in known_patterns:
            files_matching = self.root.glob(f"**/{pattern}")
            all_files.extend(list(files_matching))
        return all_files
