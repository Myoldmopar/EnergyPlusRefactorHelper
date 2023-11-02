from pathlib import Path
from unittest import TestCase

from error_refactor.source_file import SourceFile


class TestSourceFile(TestCase):
    def setUp(self):
        this_file = Path(__file__).resolve()
        self.test_file = this_file.parent / 'fake_source_folder' / 'test_file.cc'

    def test_a(self):
        sf = SourceFile(self.test_file)
        self.assertEqual(3, len(sf.identified_error_blocks))
