from pathlib import Path

from pytest import raises

from energyplus_refactor_helper.actions.base import RefactorBase
from energyplus_refactor_helper.function_call import FunctionCall


def test_default_interface():
    rb = RefactorBase()
    with raises(NotImplementedError):
        rb.run(Path(), Path(), True, True)
    fc = FunctionCall(0, 'f', 0, 0, 0, 'f(x, y)')
    assert isinstance(rb.base_function_call_visitor(fc), str)
