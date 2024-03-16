class CommandError(Exception):
    def __init__(self, command, line=None):
        message = f"Malformed command '{command}'"
        if line is not None:
            message += f" in line {line}"
        message += "."
        super().__init__(message)
