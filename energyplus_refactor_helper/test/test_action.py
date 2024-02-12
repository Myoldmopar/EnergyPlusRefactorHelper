from pathlib import Path

from pytest import raises

from energyplus_refactor_helper.action import RefactorBase, ErrorCallRefactor
from energyplus_refactor_helper.function_call import FunctionCall
from energyplus_refactor_helper.function_call_group import FunctionCallGroup


def test_default_interface():
    rb = RefactorBase()
    with raises(NotImplementedError):
        rb.run(Path(), Path(), True, True)
    fc = FunctionCall(0, 'f', 0, 0, 0, 'f(x, y)')
    assert isinstance(rb.base_function_call_visitor(fc), str)


def test_error_call_visitor():
    ecr = ErrorCallRefactor()
    s = ecr.CallSymbols
    # Severe, continue, continue, fatal
    fcs = [
        FunctionCall(s.ShowSevereError, 'ShowSevereError', 1, 0, 0, 'ShowSevereError(s, "Black");'),
        FunctionCall(s.ShowContinueError, 'ShowContinueError', 1, 0, 0, 'ShowContinueError(s, "then");'),
        FunctionCall(s.ShowContinueError, 'ShowContinueError', 1, 0, 0, 'ShowContinueError(s, "white are");'),
        FunctionCall(s.ShowFatalError, 'ShowFatalError', 1, 0, 0, 'ShowFatalError(s, "all I see");'),
    ]
    group = FunctionCallGroup()
    [group.add_function_call(f) for f in fcs]
    expected_text = 'emitErrorMessages(s, -999, {"Black", "then", "white are", "all I see"}, true);'
    resulting_text = ecr.visitor(group)
    assert expected_text == resulting_text
    # Test with preceding text
    fcs = [
        FunctionCall(s.ShowSevereError, 'ShowSevereError', 1, 0, 0, 'ShowSevereError(s, "Foo");'),
        FunctionCall(s.ShowFatalError, 'ShowFatalError', 1, 0, 3, 'Hi; ShowFatalError(s, "bar");'),
    ]
    group = FunctionCallGroup()
    [group.add_function_call(f) for f in fcs]
    expected_text = 'ShowSevereError(s, "Foo");\nHi;ShowFatalError(s, "bar");'
    resulting_text = ecr.visitor(group)
    assert expected_text == resulting_text
    # now just a standalone warning
    fcs = [
        FunctionCall(s.ShowWarningError, 'ShowWarningError', 1, 0, 0, 'ShowWarningError(s, "Foo");'),
    ]
    group = FunctionCallGroup()
    [group.add_function_call(f) for f in fcs]
    expected_text = 'emitWarningMessage(s, -999, "Foo");'
    resulting_text = ecr.visitor(group)
    assert expected_text == resulting_text
    # now just a standalone severe
    fcs = [
        FunctionCall(s.ShowSevereError, 'ShowSevereError', 1, 0, 0, 'ShowSevereError(s, "Foo");'),
    ]
    group = FunctionCallGroup()
    [group.add_function_call(f) for f in fcs]
    expected_text = 'emitErrorMessage(s, -999, "Foo", false);'
    resulting_text = ecr.visitor(group)
    assert expected_text == resulting_text
    # now just a single standalone fatal
    fcs = [
        FunctionCall(s.ShowFatalError, 'ShowFatalError', 1, 0, 0, 'ShowFatalError(s, "Foo");'),
    ]
    group = FunctionCallGroup()
    [group.add_function_call(f) for f in fcs]
    expected_text = 'emitErrorMessage(s, -999, "Foo", true);'
    resulting_text = ecr.visitor(group)
    assert expected_text == resulting_text
