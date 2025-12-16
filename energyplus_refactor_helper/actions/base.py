from pathlib import Path


class RefactorBase:
    @staticmethod
    def base_function_call_visitor(function_call) -> str:
        """
        This is a small helper function that simply takes a function call argument, and rewrites it in a functionally
        equivalent manner, returning that string.

        :param function_call: The FunctionCall instance to operate on
        ;return str: The function call in a functionally equivalent string
        """
        return function_call.rewrite()

    @staticmethod
    def base_function_group_visitor(function_group) -> str:
        individual_call_strings = []
        for i, function in enumerate(function_group.function_calls):
            full_call = function.rewrite()
            include_prefix = len(function_group.function_calls) > 0 and i > 0
            including_prefix = (function.preceding_text + full_call) if include_prefix else full_call
            individual_call_strings.append(including_prefix)
        return '\n'.join(individual_call_strings)

    def run(self, source_repo: Path, output_path: Path, edit_in_place: bool, skip_plots: bool) -> int:
        raise NotImplementedError()
