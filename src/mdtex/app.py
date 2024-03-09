#pylint: disable=E0203,E1101

import argparse
from pathlib import Path
import re

from mdtex.config import config, defaults, PATH_IO

class App:

    def __init__(self, args=None):
        if args is None:
            args = []
        self.args = self._parse_arguments(args)
        for arg, value in self.args.items():
            setattr(self, arg, value)
        self._postprocess()
    
    def __iter__(self):
        return iter({k: v for k, v in vars(self).items() if k != "args"}.items())

    @classmethod
    def _get_parser(cls):
        # pylint: disable=C0103
        _ON_OFF = ["ON", "OFF"]

        parser = argparse.ArgumentParser()
        parser.add_argument("input", action="store", nargs="?")
        parser.add_argument("-o", "--output", action="store", default=None)
        parser.add_argument("-d", "--documentclass", action="store")
        parser.add_argument("-T", "--title", action="store", default="")
        parser.add_argument("-A", "--author", action="store", default="")
        parser.add_argument("-D", "--date", action="store", default="")
        parser.add_argument("-1", "--header-one-is-title", action="store", choices=_ON_OFF)
        parser.add_argument("-e", "--escape", action="store", dest="escape_characters")
        parser.add_argument("-v", "--verbose", action="store_true")
        parser.add_argument("--use-emph", action="store", nargs='*', choices=["single", "double"], dest="use_emph")
        parser.add_argument("--pkg-fancyvrb", action="store", choices=_ON_OFF)
        parser.add_argument("--pkg-fancyvrb-args", action="store", nargs="*")
        parser.set_defaults(**defaults)
        return parser

    @staticmethod
    def _parse_arguments(args):
        parser = App._get_parser()
        namespace, unknown_args = parser.parse_known_args(args)

        if not namespace.input.lower().endswith(".md"):
            raise ValueError(
                f'Input file "{namespace.input}" must end in ".md"'
            )

        for key, value in vars(namespace).items():
            if value == "ON":
                setattr(namespace, key, True)
            elif value == "OFF":
                setattr(namespace, key, False)
        
        namespace.cmd_single = ("emph" if "single" in namespace.use_emph else "textit")
        namespace.cmd_double = ("emph" if "double" in namespace.use_emph else "textbf")
        namespace.env_verbatim = ("Verbatim" if namespace.pkg_fancyvrb else "verbatim")
        namespace.arg_verbatim = (namespace.pkg_fancyvrb_args if namespace.pkg_fancyvrb else [])

        # TODO Confuses, e.g. --headerthree with "input"...
        headers_args, _ = App._parse_headers(namespace.documentclass,
                                             namespace.header_one_is_title,
                                             unknown_args,
        )

        args = vars(namespace)
        args.update(vars(headers_args))

        return args
    
    @staticmethod
    def _parse_headers(document_class, header_one_is_title, args):
        numbers = ("zero", "one", "two", "three", "four", "five", "six")
        default_headers = (
            "part",
            "chapter",
            "section",
            "subsection",
            "subsubsection",
            "paragraph",
            "subparagraph",
            "subparagraph",
        )
        offset = 0
        if header_one_is_title:
            offset -= 1
        if document_class == "book":
            offset += -1
        elif document_class == "report":
            offset += 0
        elif document_class == "article":
            offset += 1
        else:
            raise ValueError(
                f"Wrong value for document class: {document_class}."
            )
        parser = argparse.ArgumentParser()
        parser.add_argument("--headerone",
                            action="store",
                            nargs=1,
                            default=("title"
                                     if header_one_is_title
                                     else default_headers[1 + offset]
                            ),
        )

        for i in range(2, 7):
            parser.add_argument(f"--header{numbers[i]}",
                                action="store",
                                nargs=1,
                                default=default_headers[i + offset]
            )
        return parser.parse_known_args(args)

    @staticmethod
    def _get_input_path(input_: str):
        path_in = Path(input_)
        if path_in.is_absolute():
            if path_in.exists():
                return path_in
        else:
            if (PATH_IO / path_in).exists:
                return PATH_IO / path_in
        raise FileNotFoundError(
            f"File {input_} not found."
        )

    @staticmethod
    def _get_output_path(output: str, input_path: Path):
        path_in = input_path
        dir_default = (
            path_in.parent
            if config.default_output_dir_as_input_dir
            else Path(".").absolute()
        )
        path_out = (
            Path(output)
            if output is not None
            else None
        )
        if path_out is None:
            name_out = path_in.name
            name_out = name_out.rstrip(path_in.suffix) + ".tex"
            return dir_default / name_out
        if not path_out.is_absolute():
            return dir_default / path_out
        return path_out

    def _postprocess(self):
        self.input = self._get_input_path(self.input)
        self.output = self._get_output_path(self.output, self.input)

        packages = set()
        for k, v in vars(self).items():
            match_ = re.match(r"^pkg_(.+)(?!_args)$", k)
            if match_ is not None and v is True:
                packages.add(match_.groups()[0])
        self.packages = sorted(packages)
    
    def update(self, *args, **kwargs):
        args = tuple(filter(lambda x: x is not None, args))
        if all(isinstance(arg, dict) for arg in args):
            for arg in args:
                kwargs.update(arg)
        else:
            raise TypeError(
                f"Wrong argument type: {[type(el) for el in args]}"
            )
        for key, value in kwargs.items():
            setattr(self, key, value)
