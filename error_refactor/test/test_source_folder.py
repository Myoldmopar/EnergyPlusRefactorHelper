from pathlib import Path
from unittest import TestCase

from error_refactor.source_folder import SourceFolder


class TestSourceFolder(TestCase):
    def setUp(self):
        this_file = Path(__file__).resolve()
        self.fake_source_folder = this_file.parent / 'fake_source_folder'

    def test_it_finds_matching_files_recursively(self):
        sf = SourceFolder(self.fake_source_folder)
        self.assertEqual(2, len(sf.matched_files))
