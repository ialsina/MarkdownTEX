from mdtex.config import PATH_FONTS, PATH_FONT_USAGE

class CommandError(Exception):
    def __init__(self, command, line=None):
        message = f"Malformed command '{command}'"
        if line is not None:
            message += f" in line {line}"
        message += "."
        super().__init__(message)

class NoFontFilesError(FileNotFoundError):
    def __init__(self):
        message = f"Files {PATH_FONTS} and {PATH_FONT_USAGE} must exist to use latex fonts."
        super().__init__(message)
