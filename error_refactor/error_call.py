class ErrorCallType:
    Warning = 0
    Severe = 1
    Fatal = 2


class ErrorCall:  # need to decide if this is an old call, new call, or combined
    def __init__(self):
        self.x = 1
        self.type = ErrorCallType.Warning

    def new_text(self) -> str:
        return f"{self.type}: {self.x}"
