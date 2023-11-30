from pathlib import Path
from tempfile import mkstemp
from unittest import TestCase

from error_refactor.source_file import SourceFile


class TestSourceFile(TestCase):
    def setUp(self):
        this_file = Path(__file__).resolve()
        self.test_file = this_file.parent / 'fake_source_folder' / 'test_file.cc'

    def test_basic_operation(self):
        sf = SourceFile(self.test_file)
        sf.process_error_calls_in_file()
        self.assertEqual(9, len(sf.found_errors))
        self.assertIsNotNone(sf.get_summary())

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
        sf = SourceFile(p)
        sf.process_error_calls_in_file()
        self.assertEqual(2, len(sf.found_errors))
        found_error = sf.found_errors[0]
        self.assertTrue(found_error.appears_successful)
        self.assertEqual(124, found_error.char_start_in_file)
        self.assertEqual(187, found_error.char_end_in_file)
        found_error_2 = sf.found_errors[1]
        self.assertTrue(found_error_2.appears_successful)
        self.assertEqual(250, found_error_2.char_start_in_file)
        self.assertEqual(465, found_error_2.char_end_in_file)

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
            IS,
            LONG
        )
    );
        """
        p.write_text(raw_text)
        sf = SourceFile(p)
        sf.process_error_calls_in_file()
        found_error = sf.found_errors[0]
        self.assertFalse(found_error.appears_successful)

    def test_call_type_worker_function(self):
        message = "Something - ShowContinueError(blah,"
        call, ind = SourceFile.get_call_type_and_starting_index_from_raw_line(message)
        self.assertEqual("ShowContinueError(", call)
        self.assertEqual(12, ind)

        message = "Nothing here!"
        call, ind = SourceFile.get_call_type_and_starting_index_from_raw_line(message)
        self.assertIsNone(call)
        self.assertEqual(-1, ind)
