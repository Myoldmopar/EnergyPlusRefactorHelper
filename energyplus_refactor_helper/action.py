# this file will include an abstract base class for any specific refactor
# it will, for now, also include any example refactor configs
from pathlib import Path
from typing import Type

from energyplus_refactor_helper.source_folder import SourceFolder


class RefactorBase:
    """
    This is an abstract base class for refactors in this package.  Right now it only supports finding function calls, so
    the only thing really needed from a derived class is to override the function_calls() pure virtual method here.
    There are other methods which can be used to set/override refactor parameters if needed.
    """

    # noinspection PyMethodMayBeStatic
    def file_names_to_ignore(self) -> list[str]:
        """
        This method returns a list of file names that should be ignored during this refactor.  The primary reason for
        this is to avoid having the refactor engine match the actual function definition/declaration.  By default, this
        returns an empty list, but should return file names as strings if it is overridden.

        :return: A list of file names that should be ignored during this refactor.
        """
        return []

    # noinspection PyMethodMayBeStatic
    def analysis_root_from_repo_root(self, repo_root_path: Path) -> Path:
        """
        This method returns a Path to the root of the refactor search.  The primary use of this method is to isolate the
        refactor to only a certain subdirectory.  By default, this method returns the src/EnergyPlus directory within
        the repository, but can be overridden to return any directory relative to the EnergyPlus project/repo root.

        :param repo_root_path: The root of the EnergyPlus repository/project.
        :return: A Path object relative to the passed in repository root.
        """
        return repo_root_path / 'src' / 'EnergyPlus'

    def function_calls(self) -> list[str]:  # return something better eventually
        """
        This method returns a list of function names that should be matched during this refactor.  In the future, it is
        expected that this function returns more meaningful information, but this is all that is needed right now.

        :return: A list of function names.
        """
        raise NotImplementedError()

    def run(self, source_repo: Path, output_path: Path, edit_in_place: bool) -> int:
        """
        This method performs the actual run operations based on input arguments.  The method calls (possibly overridden)
        methods to get run data, then creates a SourceFolder instance, and returns a success flag with 0 if successful
        and 1 if not.

        :param source_repo: The root of the EnergyPlus repository to operate upon.
        :param output_path: An output directory where logs and results should be dumped.
        :param edit_in_place: A flag for whether we are actually editing the repository files in place.  If not, then
                              this will mostly just result in analysis, with outputs in the output_path provided.
        :return: A status flag, 0 if successful, 1 if not.
        """
        file_names_to_ignore = self.file_names_to_ignore()
        source_path = self.analysis_root_from_repo_root(source_repo)
        sf = SourceFolder(source_path, output_path, file_names_to_ignore, self.function_calls(), edit_in_place)
        return 0 if sf.success else 1


class ErrorCallRefactor(RefactorBase):
    """
    This is a specific derived refactor class focused on error calls.  Some of the virtual methods have been overridden
    and have their own description below.
    """

    def file_names_to_ignore(self) -> list[str]:
        """
        This method returns just UtilityRoutines.cc, which is where these error functions are located.

        :return: A list with a single object, a string UtilityRoutines.cc
        """
        return ['UtilityRoutines.cc']

    def function_calls(self) -> list[str]:
        """
        This method returns all the error functions we want to match during this refactor.

        :return: A list of error function names
        """
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
