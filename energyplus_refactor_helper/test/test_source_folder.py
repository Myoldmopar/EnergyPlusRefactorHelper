from pathlib import Path
from tempfile import mkdtemp

from energyplus_refactor_helper.configs import ErrorCallStrings
from energyplus_refactor_helper.source_folder import SourceFolder


class TestSourceFolder:
    @staticmethod
    def set_up_dirs() -> tuple[Path, Path]:
        this_file = Path(__file__).resolve()
        fake_source_folder = this_file.parent / 'fake_source_folder' / 'src' / 'EnergyPlus'
        dummy_output_folder = Path(mkdtemp())
        return fake_source_folder, dummy_output_folder

    def test_it_finds_matching_files_recursively(self):
        fake_source_folder, dummy_output_folder = TestSourceFolder.set_up_dirs()
        sf = SourceFolder(fake_source_folder, [], ErrorCallStrings.all_calls())
        assert len(sf.matched_files) == 3

    def test_it_finds_matching_files_including_ignored(self):
        fake_source_folder, dummy_output_folder = TestSourceFolder.set_up_dirs()
        sf = SourceFolder(fake_source_folder, ['file_to_ignore.cc'], ErrorCallStrings.all_calls())
        assert len(sf.matched_files) == 2


    def test_full_workflow(self):
        fake_source_folder, dummy_output_folder = TestSourceFolder.set_up_dirs()
        sf = SourceFolder(fake_source_folder, ['file_to_ignore.cc'], ErrorCallStrings.all_calls())
        sf.analyze()
        sf.generate_outputs(dummy_output_folder)
        output_files_found = list(dummy_output_folder.glob('*'))
        assert len(output_files_found) > 0

    def test_it_creates_output_folder_if_not_exists(self):
        fake_source_folder, dummy_output_folder = TestSourceFolder.set_up_dirs()
        nonexistent_dummy_output_folder = dummy_output_folder / 'dummy'
        sf = SourceFolder(fake_source_folder, ['file_to_ignore.cc'], ErrorCallStrings.all_calls())
        sf.analyze()
        sf.generate_outputs(nonexistent_dummy_output_folder)
        output_files_found = list(nonexistent_dummy_output_folder.glob('*'))
        assert len(output_files_found) > 0
