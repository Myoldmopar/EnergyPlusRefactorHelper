from itertools import groupby
from typing import Optional

from energyplus_refactor_helper.function_call import FunctionCall


class FunctionCallGroup:
    def __init__(self, initial_call: Optional[FunctionCall] = None):
        """
        This class represents a contiguous chunk of function calls within a source file.  This is essentially just
        a list of function call instances, but some extra intelligence can apply specifically to a group of calls.
        so a class is here to provide that context.
        """
        self.function_calls = []
        self.started = False
        if initial_call:
            self.add_function_call(initial_call)

    def add_function_call(self, function_call_info: FunctionCall) -> None:
        """
        Add a function call instance to this chunk.
        """
        self.started = True
        self.function_calls.append(function_call_info)

    def summary_dict(self) -> dict:
        """
        This function creates a dict summary of a chunk of contiguous function calls.  It is expected this function will
        change to returning a nice structure instead of a loosely defined dictionary.

        :return: A single dictionary summary.
        """
        num_calls_in_this_chunk = len(self.function_calls)
        call_types = [e.call_type for e in self.function_calls]
        cleaned_call_types = [i[0] for i in groupby(call_types)]  # remove duplicates
        chunk_start_line = self.function_calls[0].starting_line_number
        chunk_end_line = self.function_calls[-1].ending_line_number
        try:
            concatenated_messages = ' *** '.join([e.parse_arguments()[1] for e in self.function_calls])
        except IndexError:  # pragma: no cover
            # this is almost certainly indicative of a parser problem, so we can't cover it
            raise Exception(f"Something went wrong with the arg processing for this chunk! {self.function_calls}")
        return {
            'num_calls_in_this_chunk': num_calls_in_this_chunk,
            'call_types': call_types,
            'cleaned_call_types': cleaned_call_types,
            'chunk_start_line': chunk_start_line,
            'chunk_end_line': chunk_end_line,
            'concatenated_messages': concatenated_messages
        }

    def to_json(self) -> dict:
        return {'summary': self.summary_dict(), 'original': [str(f) for f in self.function_calls]}
