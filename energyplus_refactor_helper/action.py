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

    # noinspection PyMethodMayBeStatic
    def function_visitor(self, function_call_or_group) -> str:
        """
        This method will visit _either_ each function call, or each function call group, and generate a new string
        representation of that call or group.  The object passed in is determined by the visits_each_group() member
        method on this class.  By default, it will be False, indicating that this action should operate on each function
        call.  However, if that method returns True, this method will need to expect an entire function call group.

        :param function_call_or_group: The FunctionCall or FunctionCallGroup to inspect, and from that, generate a new
                                       string representation.  By default, the base action will get visited on each
                                       function call, and generate a 'single line' version of the function call.
                                       The advantage of this is that we can verify our parsing by simply rewriting all
                                       function calls in the source code, reapplying Clang Format, and making sure we
                                       didn't break anything.
        :return: A string representation of the function call or function call group.
        """
        args = ', '.join(function_call_or_group.parse_arguments())
        return f"{function_call_or_group.function_name}({args});"

    # noinspection PyMethodMayBeStatic
    def visits_each_group(self) -> bool:
        return False

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
        sf = SourceFolder(
            source_path, output_path, file_names_to_ignore, self.function_calls(),
            edit_in_place, self.visits_each_group(), self.function_visitor
        )
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

    def function_visitor(self, function_group) -> str:
        """
        For this action class, this function will be visited for each function call "group".  This function will assess
        the function group, looking for different ways to rewrite the group as a new string.  For right now, this will
        simply iterate over the function group as a whole and rewrite each function call on a new line.  This allows for
        a nice quick test where we can re-apply Clang Format and get back nearly identical code.  In upcoming versions,
        this function will instead group multiple function calls into a single new interface with the messages passed as
        an initializer-list-based array of strings, and also a (for now) dummy error code.  In the final version, this
        will write correct error codes.

        :param function_group: The FunctionCallGroup to inspect, and from that, generate a new string representation.
        :return: A string representation of the function call group.
        """
        individual_call_strings = []
        for i, function in enumerate(function_group.function_calls):
            args = ', '.join(function.parse_arguments())
            full_call = f"{function.function_name}({args});"
            include_prefix = len(function_group.function_calls) > 0 and i > 0
            including_prefix = (function.preceding_text + full_call) if include_prefix else full_call
            individual_call_strings.append(including_prefix)
        return '\n'.join(individual_call_strings)

    # noinspection PyMethodMayBeStatic
    def visits_each_group(self) -> bool:
        return True


all_actions: dict[str, Type[RefactorBase]] = {
    'error_call_refactor': ErrorCallRefactor
}
