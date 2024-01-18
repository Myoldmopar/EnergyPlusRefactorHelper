from energyplus_refactor_helper.logger import logger


class FunctionCall:

    MAX_LINES_FOR_SINGLE_CALL = 13  # to detect/avoid parsing issues

    def __init__(self, call: int, line_start: int, file_start_index: int, line_start_index: int, first_line_text: str):
        """
        This class represents a single function call in the EnergyPlus source code.
        The parsing algorithms here rely on specific EnergyPlus source code style/structure assumptions, and are surely
        not applicable to generic codebases.  In the future, a more formal C++ parser may be added.

        To construct a function call, you provide the first line of code containing the function call,
        as well position details, then continue adding lines of text holding the function call, and then finalize the
        function call when the end is reached.  The function call can then be parsed into arguments using methods here.

        :param call: This represents an integer call type, which is essentially the index of the function in the
                     derived :meth:`RefactorBase.function_calls()` method.
        :param line_start: This is the 1-based line number where this function call starts in the file.
        :param file_start_index: This is the character index in the raw file text where the function call starts.
        :param line_start_index: This is the character index in the first line of the function call where the
                                 call starts
        :param first_line_text: This is the raw first line text where the function call starts.
        """
        self.call_type = call
        self.multiline_text = [first_line_text]
        self.starting_line_number = line_start
        self.ending_line_number = line_start  # initialize here
        self.char_start_in_file = file_start_index
        self.char_start_first_line = line_start_index
        self.char_end_in_file = -1
        self.appears_successful = True

    def add_to_multiline_text(self, line_content: str) -> None:
        """
        After construction of a function call, add continuing lines to the function call by calling this method.

        :param line_content: Add continuation lines of a multi-line function call using this method.
        :return: None
        """
        self.ending_line_number += 1
        self.multiline_text.append(line_content)

    def finalize(self, end_character_index: int, appears_successful: bool) -> None:
        """
        Once a function call reaches the end, call this method to "finalize" the structure.  This function accepts a
        flag to indicate if the function call parsing appeared successful.  This is useful when a function call extends
        too many lines, implying a parsing problem.

        :param end_character_index: The character index of the final line of the function call where the call ends
        :param appears_successful: A true/false flag for whether the parse "appears" successful.
        :return: None
        """
        self.char_end_in_file = end_character_index
        self.appears_successful = appears_successful

    def as_cleaned_multiline(self) -> list[str]:
        """
        After a function call has been finalized, this function provides the function call formatted as a sanitized
        multiline list of strings.

        :return: A list of strings represented sanitized lines of the function call.
        """
        skip_first_line_to_call_start = []
        for i, t in enumerate(self.multiline_text):
            this_line_content = t[self.char_start_first_line:].strip() if i == 0 else t.strip()
            skip_first_line_to_call_start.append(this_line_content)
        return [x.strip() for x in skip_first_line_to_call_start]

    def as_single_line(self) -> str:
        """
        After a function call has been finalized, this function provides the function call formatted as a single line.

        :return: A single string representation of the function call.
        """
        return ''.join(self.as_cleaned_multiline()).strip()

    def parse_arguments(self) -> list[str]:
        """
        After a function call has been finalized, this method can be used to parse the arguments of the call into a
        list of strings.  This parsing takes advantage of some assumptions about the way EnergyPlus enforces code style
        and structure.  (Such as no C++ style comments allowed, etc.)

        :return: A list of string arguments to the function call.
        """
        one_string = '\n'.join(self.as_cleaned_multiline())
        args = []
        current_arg = ""
        grouping_stack = []
        ignore_next_char = False
        reached_args = False
        about_to_enter_string_literal = False
        reading_comment_until_new_line = False
        for i, c in enumerate(one_string):
            inside_literal = "\"" in grouping_stack or '\'' in grouping_stack
            inside_raw_literal = 'R"(' in grouping_stack
            if not reached_args:  # haven't reached the args yet, just wait for first parenthesis
                if c == '(':
                    grouping_stack.append('(')
                    reached_args = True
            elif reading_comment_until_new_line:
                if c == '\n':
                    reading_comment_until_new_line = False
            elif inside_raw_literal:
                current_arg += c
                if c == '"' and one_string[i-1] == ')':
                    grouping_stack.pop()
            elif inside_literal and c == '\\':
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
                    if about_to_enter_string_literal:
                        grouping_stack.append('R"(')
                        about_to_enter_string_literal = False
                    else:
                        grouping_stack.append(c)
            elif inside_literal:
                current_arg += c
            elif c == '(':
                current_arg += c
                grouping_stack.append(c)
            elif c == ')':
                if grouping_stack[-1] == '(':
                    grouping_stack.pop()
                else:  # pragma: no cover
                    logger.log("UNBALANCED PARENTHESES; PROBABLY PARSER PROBLEM!")
                    return []  # this really should not happen
                if len(grouping_stack) == 0:  # reached the end
                    args.append(current_arg)
                    break
                current_arg += c
            elif c == ',' and len(grouping_stack) == 1:
                args.append(current_arg)
                current_arg = ''
            elif c == 'R' and one_string[i+1] == '"' and one_string[i+2] == '(':
                # it appears we are about to enter a raw literal
                about_to_enter_string_literal = True
                current_arg += c
            elif c == '/' and one_string[i+1] == '/':
                reading_comment_until_new_line = True
            elif c == '\n':
                continue  # just eat the newline
            else:
                current_arg += c
        return [a.strip() for a in args]

    def __str__(self):
        """String representation summary of the function call"""
        return f"{self.starting_line_number} - {self.ending_line_number} : {self.as_single_line()[:35]}"
