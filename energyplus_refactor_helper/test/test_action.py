from pathlib import Path

from pytest import raises

from energyplus_refactor_helper.action import RefactorBase
from energyplus_refactor_helper.function_call import FunctionCall


class TestActionBase:

    def test_interface(self):
        rb = RefactorBase()
        assert isinstance(rb.file_names_to_ignore(), list)
        assert isinstance(rb.analysis_root_from_repo_root(Path('dummy')), Path)
        assert isinstance(rb.visits_each_group(), bool)
        fc = FunctionCall(0, 'f(x, y);', 0, 0, 0, 'x')
        assert isinstance(rb.visitor(fc), str)
        with raises(NotImplementedError):
            rb.function_calls()
