from energyplus_refactor_helper.actions.error_calls import ErrorCallRefactor
from energyplus_refactor_helper.function_call import FunctionCall
from energyplus_refactor_helper.function_call_group import FunctionCallGroup


def test_error_code_lookup():
    # check that invalid is -999, although we probably won't ever hit this
    assert ErrorCallRefactor.NewErrorCodes.get_value('error_code_unclassified') == -999
    # otherwise just check a valid entry or two and ensure it returns an int
    assert isinstance(ErrorCallRefactor.NewErrorCodes.get_value('error_code_input_invalid'), int)
    assert isinstance(ErrorCallRefactor.NewErrorCodes.get_value('error_code_runtime_general'), int)
    # and check that it throws on a bad entry
    try:
        ErrorCallRefactor.NewErrorCodes.get_value('something_invalid_here')
    except ValueError:
        pass
    else:  # pragma: no cover
        # this shouldn't ever be hit in unit tests, so we need to ignore it
        assert False, "Invalid string lookup in NewErrorCodes.get_value did not throw as expected"


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
    # expected_text = 'emitErrorMessages(s, -999, {"Black", "then", "white are", "all I see"}, true);'
    resulting_text = ecr.visitor(group)
    assert '{"Black", "then", "white are", "all I see"}, true' in resulting_text
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
    # a multi-call warning
    fcs = [
        FunctionCall(s.ShowWarningMessage, 'ShowWarningMessage', 1, 0, 0, 'ShowWarningMessage(s, "Hello");'),
        FunctionCall(s.ShowContinueError, 'ShowContinueError', 1, 0, 0, 'ShowContinueError(s, "world");'),
    ]
    group = FunctionCallGroup()
    [group.add_function_call(f) for f in fcs]
    # expected_text = 'emitWarningMessages(s, -999, {"Hello", "world"});'
    resulting_text = ecr.visitor(group)
    assert '{"Hello", "world"}' in resulting_text
    # now just a standalone warning
    fcs = [
        FunctionCall(s.ShowWarningMessage, 'ShowWarningMessage', 1, 0, 0, 'ShowWarningMessage(s, "Foo");'),
    ]
    group = FunctionCallGroup()
    [group.add_function_call(f) for f in fcs]
    # expected_text = 'emitWarningMessage(s, -999, "Foo");'
    resulting_text = ecr.visitor(group)
    assert '"Foo");' in resulting_text
    # now just a standalone warning error
    fcs = [
        FunctionCall(s.ShowWarningError, 'ShowWarningError', 1, 0, 0, 'ShowWarningError(s, "Foo");'),
    ]
    group = FunctionCallGroup()
    [group.add_function_call(f) for f in fcs]
    # expected_text = 'emitWarningMessage(s, -999, "Foo", true);'
    resulting_text = ecr.visitor(group)
    assert '"Foo", true' in resulting_text
    # now just a standalone severe
    fcs = [
        FunctionCall(s.ShowSevereError, 'ShowSevereError', 1, 0, 0, 'ShowSevereError(s, "Foo");'),
    ]
    group = FunctionCallGroup()
    [group.add_function_call(f) for f in fcs]
    # expected_text = 'emitErrorMessage(s, -999, "Foo", false);'
    resulting_text = ecr.visitor(group)
    assert '"Foo", false' in resulting_text
    # now just a single standalone fatal
    fcs = [
        FunctionCall(s.ShowFatalError, 'ShowFatalError', 1, 0, 0, 'ShowFatalError(s, "Foo");'),
    ]
    group = FunctionCallGroup()
    [group.add_function_call(f) for f in fcs]
    # expected_text = 'emitErrorMessage(s, -999, "Foo", true);'
    resulting_text = ecr.visitor(group)
    assert '"Foo", true' in resulting_text
