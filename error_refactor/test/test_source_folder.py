from pathlib import Path
from tempfile import mkdtemp
from unittest import TestCase

from error_refactor.source_folder import SourceFolder


class TestSourceFolder(TestCase):
    def setUp(self):
        this_file = Path(__file__).resolve()
        self.fake_source_folder = this_file.parent / 'fake_source_folder'
        self.dummy_output_folder = Path(mkdtemp())

    def test_it_finds_matching_files_recursively(self):
        sf = SourceFolder(self.fake_source_folder, ['file_to_ignore.cc'])
        self.assertEqual(2, len(sf.matched_files))

    def test_full_workflow(self):
        sf = SourceFolder(self.fake_source_folder, ['file_to_ignore.cc'])
        sf.analyze()
        sf.generate_outputs(self.dummy_output_folder)
        output_files_found = list(self.dummy_output_folder.glob('*'))
        self.assertEqual(3, len(output_files_found))
