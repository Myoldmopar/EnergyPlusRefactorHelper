from energyplus_refactor_helper.actions.base import RefactorBase
from energyplus_refactor_helper.actions.listing import all_actions


def test_listing_response():
    assert isinstance(all_actions, dict)
    for action in all_actions:
        assert isinstance(action, str)
        assert issubclass(all_actions[action], RefactorBase)
