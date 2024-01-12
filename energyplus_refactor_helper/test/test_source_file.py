from pathlib import Path
from tempfile import mkstemp

from energyplus_refactor_helper.configs import ErrorCallStrings
from energyplus_refactor_helper.source_file import SourceFile

this_file = Path(__file__).resolve()
test_file = this_file.parent / 'fake_source_folder' / 'src' / 'EnergyPlus' / 'test_file.cc'


class TestSourceFile:

    def test_basic_operation(self):
        sf = SourceFile(test_file, ErrorCallStrings.all_calls())
        sf.find_functions_in_original_text()
        assert len(sf.found_functions) == 9
        assert sf.preview() is not None

    def test_complex_ish_file(self):
        _, file_path = mkstemp()
        p = Path(file_path)
        raw_text = """// INCLUDES
#include <string>

namespace UnitarySystems {
    Object *Object::factory(std::string objectName)
    {
        ShowSevereError(state, format("Factory Error: {}", objectName));
        return nullptr;
    }

    void func()
    {
        ShowContinueError(state,
            format(
                "It might be this: {} or that: {}",
                state.data->Node(1).Temp,
                state.data->CoolVector[x].attributeY
            )
        );
    }
}
"""
        p.write_text(raw_text)
        sf = SourceFile(p, ErrorCallStrings.all_calls())
        sf.find_functions_in_original_text()
        assert len(sf.found_functions) == 2
        found_error = sf.found_functions[0]
        assert found_error.appears_successful
        assert found_error.char_start_in_file == 124
        assert found_error.char_end_in_file == 187
        found_error_2 = sf.found_functions[1]
        assert found_error_2.appears_successful
        assert found_error_2.char_start_in_file == 250
        assert found_error_2.char_end_in_file == 465

    def test_last_error_group_has_multiple_errors(self):
        _, file_path = mkstemp()
        p = Path(file_path)
        raw_text = """
void func() {
    ShowSevereError(state, format("Factory Error: {}", objectName));
    int i = 1;
    ShowSevereError(state, format("Factory Error: {}", objectName));
    ShowSevereError(state, format("Factory Error: {}", objectName));
}
"""
        p.write_text(raw_text)
        sf = SourceFile(p, ErrorCallStrings.all_calls())
        sf.find_functions_in_original_text()
        assert len(sf.found_functions) == 3
        error_call_info = sf.get_call_info_dict()
        assert len(error_call_info) == 2
        error_preview = sf.preview()
        assert isinstance(error_preview, str)

    def test_error_after_text(self):
        _, file_path = mkstemp()
        p = Path(file_path)
        raw_text = """
          if (j > NumCur) ShowFatalError(state, "Out of range, too high (FAN) in ADS simulation");
        """
        p.write_text(raw_text)
        sf = SourceFile(p, ErrorCallStrings.all_calls())
        sf.find_functions_in_original_text()
        assert len(sf.found_functions) == 1
        found_error = sf.found_functions[0]
        assert found_error.appears_successful
        assert found_error.char_start_in_file == 27
        assert found_error.char_end_in_file == 98

    def test_skips_long_parse(self):
        _, file_path = mkstemp()
        p = Path(file_path)
        raw_text = """
    ShowContinueError(state,
        format(
            "It might be this: {} or that: {}",
            state.data->Node(1).Temp,
            state.data->CoolVector[x].attributeY,
            OK,
            SO,
            WELL,
            THIS,
            THIS,
            THIS,
            THIS,
            THIS,
            IS,
            LONG
        )
    );
        """
        p.write_text(raw_text)
        sf = SourceFile(p, ErrorCallStrings.all_calls())
        sf.find_functions_in_original_text()
        found_error = sf.found_functions[0]
        assert not found_error.appears_successful

    def test_call_type_worker_function(self):
        message = "Something - ShowContinueError(blah,"
        call, ind = SourceFile.get_call_type_and_starting_index_from_raw_line(ErrorCallStrings.all_calls(), message)
        assert call == 3
        assert ind == 12

        message = "Nothing here!"
        call, ind = SourceFile.get_call_type_and_starting_index_from_raw_line(ErrorCallStrings.all_calls(), message)
        assert call is None
        assert ind == -1
