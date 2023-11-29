from typing import List


class ErrorCallStrings:
    ShowFatalError = "ShowFatalError("
    ShowSevereError = "ShowSevereError("
    ShowSevereMessage = "ShowSevereMessage("
    ShowContinueError = "ShowContinueError("
    ShowContinueErrorTimeStamp = "ShowContinueErrorTimeStamp("
    ShowMessage = "ShowMessage("
    ShowWarningError = "ShowWarningError("
    ShowWarningMessage = "ShowWarningMessage("
    ShowRecurringSevereErrorAtEnd = "ShowRecurringSevereErrorAtEnd("
    ShowRecurringWarningErrorAtEnd = "ShowRecurringWarningErrorAtEnd("
    ShowRecurringContinueErrorAtEnd = "ShowRecurringContinueErrorAtEnd("
    StoreRecurringErrorMessage = "StoreRecurringErrorMessage("
    ShowErrorMessage = "ShowErrorMessage("
    SummarizeErrors = "SummarizeErrors("
    ShowRecurringErrors = "ShowRecurringErrors("
    ShowSevereDuplicateName = "ShowSevereDuplicateName("
    ShowSevereItemNotFound = "ShowSevereItemNotFound("
    ShowSevereInvalidKey = "ShowSevereInvalidKey("
    ShowSevereInvalidBool = "ShowSevereInvalidBool("
    ShowSevereEmptyField = "ShowSevereEmptyField("
    ShowWarningInvalidKey = "ShowWarningInvalidKey("
    ShowWarningInvalidBool = "ShowWarningInvalidBool("
    ShowWarningEmptyField = "ShowWarningEmptyField("
    ShowWarningItemNotFound = "ShowWarningItemNotFound("

    @staticmethod
    def all_calls() -> List[str]:
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


class ErrorCallType:
    Warning = 0
    Severe = 1
    Fatal = 2


class ErrorCall:
    MAX_LINES_FOR_ERROR_CALL = 8  # to detect/avoid parsing errors

    def __init__(self, line_start: int, char_start_in_file: int, char_start_first_line: int, first_line_raw_text: str):
        self.multiline_text = [first_line_raw_text]
        self.line_start = line_start
        self.char_start_in_file = char_start_in_file
        self.char_start_first_line = char_start_first_line
        self.line_end: int = -1
        self.char_end = -1
        self.appears_successful = True

    def add_to_multiline_text(self, line_content: str) -> None:
        self.multiline_text.append(line_content)

    def complete(self, line_number: int, end_character_index: int, appears_successful: bool) -> None:
        self.line_end = line_number
        self.char_end = end_character_index
        self.appears_successful = appears_successful

    def one_line_call(self) -> str:
        skip_first_line_to_call_start = []
        for i, t in enumerate(self.multiline_text):
            if i == 0:
                skip_first_line_to_call_start.append(t[self.char_start_first_line:].strip())
            else:
                skip_first_line_to_call_start.append(t.strip())
        return ''.join(skip_first_line_to_call_start).strip()

    def parse_arguments(self) -> List[str]:
        single_liner = self.one_line_call()
        args = []
        current_arg = ""
        grouping_stack = []
        ignore_next_char = False
        reached_args = False
        for c in single_liner:
            inside_literal = "\"" in grouping_stack or '\'' in grouping_stack
            if not reached_args:  # haven't reached the args yet, just wait for first parenthesis
                if c == '(':
                    grouping_stack.append('(')
                    reached_args = True
                continue
            if inside_literal and c == '\\':
                current_arg += c
                ignore_next_char = True
            elif ignore_next_char:
                current_arg += c
                ignore_next_char = False
            elif c == '\"':
                current_arg += c
                if grouping_stack[-1] == '\"':
                    grouping_stack.pop()
                else:
                    grouping_stack.append(c)
            # elif c == '\'':  # no apostrophe for c strings
            #     current_arg += c
            #     if grouping_stack[-1] == '\'':
            #         grouping_stack.pop()
            #     else:
            #         grouping_stack.append(c)
            elif inside_literal:
                current_arg += c
            elif c == '(':
                current_arg += c
                grouping_stack.append(c)
            elif c == ')':
                if grouping_stack[-1] == '(':
                    grouping_stack.pop()
                else:  # pragma: no cover
                    print("UNBALANCED PARENTHESES!")
                    return []  # this really should not happen
                if len(grouping_stack) == 0:  # reached the end
                    args.append(current_arg)
                    break
                current_arg += c
            elif c == ',' and len(grouping_stack) == 1:
                args.append(current_arg)
                current_arg = ''
            else:
                current_arg += c
        return [a.strip() for a in args]
