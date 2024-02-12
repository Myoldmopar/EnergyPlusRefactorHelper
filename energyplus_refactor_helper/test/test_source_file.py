from pathlib import Path
from tempfile import mkstemp

from energyplus_refactor_helper.action import ErrorCallRefactor
from energyplus_refactor_helper.function_call import FunctionCall
from energyplus_refactor_helper.function_call_group import FunctionCallGroup
from energyplus_refactor_helper.source_file import SourceFile

this_file = Path(__file__).resolve()
test_file = this_file.parent / 'fake_source_folder' / 'src' / 'EnergyPlus' / 'test_file.cc'
funcs = ErrorCallRefactor().function_calls()  # TODO: use a custom list not a demo action
group_flag = ErrorCallRefactor().visits_each_group()
function_visitor = ErrorCallRefactor().visitor


def test_basic_operation():
    sf = SourceFile(test_file, funcs)
    sf.find_functions_in_original_text()
    assert len(sf.found_functions) == 9


def test_complex_ish_file():
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
    sf = SourceFile(p, funcs)
    sf.find_functions_in_original_text()
    assert len(sf.found_functions) == 2
    found_error = sf.found_functions[0]
    assert found_error.appears_successful
    assert found_error.char_start_in_file == 112
    assert found_error.char_end_in_file == 175
    found_error_2 = sf.found_functions[1]
    assert found_error_2.appears_successful
    assert found_error_2.char_start_in_file == 218
    assert found_error_2.char_end_in_file == 409


def test_last_error_group_has_multiple_errors():
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
    sf = SourceFile(p, funcs)
    sf.find_functions_in_original_text()
    assert len(sf.found_functions) == 3
    error_call_info = sf.get_function_call_groups()
    assert len(error_call_info) == 2


def test_error_after_text():
    _, file_path = mkstemp()
    p = Path(file_path)
    raw_text = """
      if (j > NumCur) ShowFatalError(state, "Out of range, too high (FAN) in ADS simulation");
    """
    p.write_text(raw_text)
    sf = SourceFile(p, funcs)
    sf.find_functions_in_original_text()
    assert len(sf.found_functions) == 1
    found_error = sf.found_functions[0]
    assert found_error.appears_successful
    assert found_error.char_start_in_file == 23
    assert found_error.char_end_in_file == 94


def test_skips_long_parse():
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
    sf = SourceFile(p, funcs)
    found_error = sf.found_functions[0]
    assert not found_error.appears_successful


def test_call_type_worker_function():
    message = "Something - ShowContinueError(blah,"
    call, ind = SourceFile.find_function_in_raw_line(funcs, message)
    assert call == 3
    assert ind == 12

    message = "Nothing here!"
    call, ind = SourceFile.find_function_in_raw_line(funcs, message)
    assert call is None
    assert ind == -1


def f_visitor(f: FunctionCall) -> str:  # basically reproduce default action
    args = ', '.join(f.parse_arguments())
    return f"{f.function_name}({args});"


def f_group_visitor(f: FunctionCallGroup) -> str:  # do a dumb example
    starting_char = f.function_calls[0].parse_arguments()[0][0]  # first character of first arg
    last_char = f.function_calls[-1].parse_arguments()[-1][-1]  # last character of last arg
    return f"{starting_char}{last_char}"


def test_new_file_text_function_based():
    _, file_path = mkstemp()
    p = Path(file_path)
    raw_text = "ShowContinueError(s, \nx);"
    p.write_text(raw_text)
    sf = SourceFile(p, funcs)
    sf.write_new_text_to_file(f_visitor, False)
    assert "ShowContinueError(s, x);" in p.read_text()


def test_new_file_text_group_based():
    _, file_path = mkstemp()
    p = Path(file_path)
    raw_text = "ShowContinueError(s, \nx);"
    p.write_text(raw_text)
    sf = SourceFile(p, funcs)
    sf.write_new_text_to_file(f_group_visitor, True)
    assert "sx" in p.read_text()
