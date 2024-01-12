# this file will include an abstract base class for any specific refactor
# it will, for now, also include any example refactor configs
from pathlib import Path
from typing import Type

from energyplus_refactor_helper.source_folder import SourceFolder


class ErrorCallStrings:
    ShowFatalError = "ShowFatalError("
    EnumShowFatalError = 0
    ShowSevereError = "ShowSevereError("
    EnumShowSevereError = 1
    ShowSevereMessage = "ShowSevereMessage("
    EnumShowSevereMessage = 2
    ShowContinueError = "ShowContinueError("
    EnumShowContinueError = 3
    ShowContinueErrorTimeStamp = "ShowContinueErrorTimeStamp("
    EnumShowContinueErrorTimeStamp = 4
    ShowMessage = "ShowMessage("
    EnumShowMessage = 5
    ShowWarningError = "ShowWarningError("
    EnumShowWarningError = 6
    ShowWarningMessage = "ShowWarningMessage("
    EnumShowWarningMessage = 7
    ShowRecurringSevereErrorAtEnd = "ShowRecurringSevereErrorAtEnd("
    EnumShowRecurringSevereErrorAtEnd = 8
    ShowRecurringWarningErrorAtEnd = "ShowRecurringWarningErrorAtEnd("
    EnumShowRecurringWarningErrorAtEnd = 9
    ShowRecurringContinueErrorAtEnd = "ShowRecurringContinueErrorAtEnd("
    EnumShowRecurringContinueErrorAtEnd = 10
    StoreRecurringErrorMessage = "StoreRecurringErrorMessage("
    EnumStoreRecurringErrorMessage = 11
    ShowErrorMessage = "ShowErrorMessage("
    EnumShowErrorMessage = 12
    SummarizeErrors = "SummarizeErrors("
    EnumSummarizeErrors = 13
    ShowRecurringErrors = "ShowRecurringErrors("
    EnumShowRecurringErrors = 14
    ShowSevereDuplicateName = "ShowSevereDuplicateName("
    EnumShowSevereDuplicateName = 15
    ShowSevereItemNotFound = "ShowSevereItemNotFound("
    EnumShowSevereItemNotFound = 16
    ShowSevereInvalidKey = "ShowSevereInvalidKey("
    EnumShowSevereInvalidKey = 17
    ShowSevereInvalidBool = "ShowSevereInvalidBool("
    EnumShowSevereInvalidBool = 18
    ShowSevereEmptyField = "ShowSevereEmptyField("
    EnumShowSevereEmptyField = 19
    ShowWarningInvalidKey = "ShowWarningInvalidKey("
    EnumShowWarningInvalidKey = 20
    ShowWarningInvalidBool = "ShowWarningInvalidBool("
    EnumShowWarningInvalidBool = 21
    ShowWarningEmptyField = "ShowWarningEmptyField("
    EnumShowWarningEmptyField = 22
    ShowWarningItemNotFound = "ShowWarningItemNotFound("
    EnumShowWarningItemNotFound = 23

    @staticmethod
    def all_calls() -> list[str]:
        return [
            ErrorCallStrings.ShowFatalError,
            ErrorCallStrings.ShowSevereError,
            ErrorCallStrings.ShowSevereMessage,
            ErrorCallStrings.ShowContinueError,
            ErrorCallStrings.ShowContinueErrorTimeStamp,
            ErrorCallStrings.ShowMessage,
            ErrorCallStrings.ShowWarningError,
            ErrorCallStrings.ShowWarningMessage,
            ErrorCallStrings.ShowRecurringSevereErrorAtEnd,
            ErrorCallStrings.ShowRecurringWarningErrorAtEnd,
            ErrorCallStrings.ShowRecurringContinueErrorAtEnd,
            ErrorCallStrings.StoreRecurringErrorMessage,
            ErrorCallStrings.ShowErrorMessage,
            ErrorCallStrings.SummarizeErrors,
            ErrorCallStrings.ShowRecurringErrors,
            ErrorCallStrings.ShowSevereDuplicateName,
            ErrorCallStrings.ShowSevereItemNotFound,
            ErrorCallStrings.ShowSevereInvalidKey,
            ErrorCallStrings.ShowSevereInvalidBool,
            ErrorCallStrings.ShowSevereEmptyField,
            ErrorCallStrings.ShowWarningInvalidKey,
            ErrorCallStrings.ShowWarningInvalidBool,
            ErrorCallStrings.ShowWarningEmptyField,
            ErrorCallStrings.ShowWarningItemNotFound
        ]


class RefactorBase:
    def __init__(self):
        self.hello = True

    def run_with_args(self, source_repo: Path, output_path: Path, edit_in_place: bool) -> int:  # pragma: no cover
        raise NotImplementedError()


class ErrorCallRefactor(RefactorBase):

    def __init__(self):
        super().__init__()

    def run_with_args(self, source_repo: Path, output_path: Path, edit_in_place: bool) -> int:
        file_names_to_ignore = ['UtilityRoutines.cc']
        source_path = source_repo / 'src' / 'EnergyPlus'
        sf = SourceFolder(source_path, file_names_to_ignore, ErrorCallStrings.all_calls())
        sf.analyze()
        sf.generate_outputs(output_path)
        return 0


all_configs: dict[str, Type[RefactorBase]] = {
    'error_call_refactor': ErrorCallRefactor
}
