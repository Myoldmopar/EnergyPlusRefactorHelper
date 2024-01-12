# this file will include an abstract base class for any specific refactor
# it will, for now, also include any example refactor configs
from pathlib import Path
from typing import Type

from energyplus_refactor_helper.source_folder import SourceFolder


class RefactorBase:

    # noinspection PyMethodMayBeStatic
    def file_names_to_ignore(self) -> list[str]:
        return []

    # noinspection PyMethodMayBeStatic
    def analysis_root_from_repo_root(self, repo_root_path: Path) -> Path:
        return repo_root_path / 'src' / 'EnergyPlus'

    def function_calls(self) -> list[str]:  # return something better eventually
        raise NotImplementedError()

    def run(self, source_repo: Path, output_path: Path, edit_in_place: bool) -> int:
        file_names_to_ignore = self.file_names_to_ignore()
        source_path = self.analysis_root_from_repo_root(source_repo)
        sf = SourceFolder(source_path, output_path, file_names_to_ignore, self.function_calls(), edit_in_place)
        return 0 if sf.success else 1


class ErrorCallRefactor(RefactorBase):

    def file_names_to_ignore(self) -> list[str]:
        return ['UtilityRoutines.cc']

    def function_calls(self) -> list[str]:
        return [
            "ShowFatalError",
            "ShowSevereError",
            "ShowSevereMessage",
            "ShowContinueError",
            "ShowContinueErrorTimeStamp",
            "ShowMessage",
            "ShowWarningError",
            "ShowWarningMessage",
            "ShowRecurringSevereErrorAtEnd",
            "ShowRecurringWarningErrorAtEnd",
            "ShowRecurringContinueErrorAtEnd",
            "StoreRecurringErrorMessage",
            "ShowErrorMessage",
            "SummarizeErrors",
            "ShowRecurringErrors",
            "ShowSevereDuplicateName",
            "ShowSevereItemNotFound",
            "ShowSevereInvalidKey",
            "ShowSevereInvalidBool",
            "ShowSevereEmptyField",
            "ShowWarningInvalidKey",
            "ShowWarningInvalidBool",
            "ShowWarningEmptyField",
            "ShowWarningItemNotFound"
        ]


all_actions: dict[str, Type[RefactorBase]] = {
    'error_call_refactor': ErrorCallRefactor
}
