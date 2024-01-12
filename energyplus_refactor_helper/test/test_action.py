from pathlib import Path

from pytest import raises

from energyplus_refactor_helper.action import RefactorBase


class TestActionBase:

    def test_interface(self):
        rb = RefactorBase()
        assert isinstance(rb.file_names_to_ignore(), list)
        assert isinstance(rb.analysis_root_from_repo_root(Path('dummy')), Path)
        with raises(NotImplementedError):
            rb.function_calls()
