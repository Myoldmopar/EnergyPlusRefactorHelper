from typing import Type

from energyplus_refactor_helper.actions.base import RefactorBase
from energyplus_refactor_helper.actions.error_calls import ErrorCallRefactor


all_actions: dict[str, Type[RefactorBase]] = {
    'error_call_refactor': ErrorCallRefactor
}
