# pylint: disable=E0203,E1101

import argparse
from pathlib import Path

from mdtex.config import config, defaults, packages, PATH_IO

_ON_OFF = ["ON", "OFF"]
_NUMBERS = ("zero", "one", "two", "three", "four", "five", "six")
_DOCUMENT_CLASSES = ("book", "report", "article")
_DEFAULT_HEADERS = (
    "part",
    "chapter",
    "section",
    "subsection",
    "subsubsection",
    "paragraph",
    "subparagraph",
    "subparagraph",
)


def get_parsers():

    parser = argparse.ArgumentParser(add_help=True, formatter_class=argparse.RawTextHelpFormatter)

    subparsers = parser.add_subparsers()
    parser_main = subparsers.add_parser("main")
    parser_main.add_argument("input", action="store", metavar="INPUT")
    parser_main.add_argument("-o", "--output", action="store", default=None, metavar="OUTPUT")
    parser_main.add_argument("-d", "--documentclass", action="store", choices=_DOCUMENT_CLASSES, metavar="DOCUMENTCLASS")
    parser_main.add_argument("-T", "--title", action="store", default="", metavar="TITLE")
    parser_main.add_argument("-A", "--author", action="store", default="", metavar="AUTHOR")
    parser_main.add_argument("-D", "--date", action="store", default="", metavar="DATE")
    parser_main.add_argument("-1", "--header-one-is-title", action="store", choices=_ON_OFF, metavar="HEADER_ONE_IS_TITLE")
    parser_main.add_argument("-e", "--escape", action="store", dest="escape_characters", metavar="ESCAPE_CHARACTERS")
    parser_main.add_argument("-L", "--latex-symb", action="store", choices=_ON_OFF, metavar="LATEX_SYMB")
    parser_main.add_argument("-v", "--verbose", action="store_true")
    parser_main.add_argument("--use-emph",
                            action="store",
                            nargs='*',
                            choices=["single", "double"],
                            dest="use_emph",
                            )
    parser_main.set_defaults(**{k: v for k, v in defaults.items() if not k.startswith("pkg_")})

    parser_package = subparsers.add_parser("package")

    for pkg in packages.on_off:
        parser_package.add_argument(f"--pkg-{pkg}", action="store", choices=_ON_OFF, metavar="PKG")
        parser_package.add_argument(f"--pkg-{pkg}-args", action="store", metavar="PKGARGS") #, nargs="*"

    for functionality, pkglst in packages.functionality.items():
        parser_package.add_argument(f"--pkg-{functionality}", action="store", choices=pkglst, metavar="PKG")
        for pkg in pkglst:
            parser_package.add_argument(f"--pkg-{pkg}-args", action="store", metavar="PKGARGS") #, nargs="*"

    parser_package.set_defaults(**{k: v for k, v in defaults.items() if k.startswith("pkg_")})

    parser_header = subparsers.add_parser("header")
    for number in _NUMBERS:
        parser_header.add_argument(f"--header{number}", action="store", metavar="HEADER")
    
    return parser, parser_main, parser_package, parser_header

parser, parser_main, parser_package, parser_header = get_parsers()


class App:

    def __init__(self, args=None):
        if args is None:
            args = []
        namespace, unknown_args = self._parse_arguments(args)
        self._set_args(namespace)
        header_args, unknown_args = self._parse_headers(unknown_args)
        self._set_args(header_args)
        package_args, used_packages = self._parse_package_args(unknown_args)
        self.packages = used_packages
        # TODO Confuses, e.g. --headerthree with "input"...
        self.pkg = {}
        self.cmd = {}
        self.env = {}
        self.env_args = {}
        self._process_package_args(package_args)
    
    def _set_args(self, args):
        for arg, value in vars(args).items():
            setattr(self, arg, value)

    def _parse_arguments(self, args):
        namespace, unknown_args = parser.parse_known_args(["main"] + args)
        if not namespace.input.lower().endswith(".md"):
            raise ValueError(
                f'Input file "{namespace.input}" must end in ".md"'
            )
        namespace = self._transform_namespace(namespace)
        namespace.input = self._normalize_input_path(namespace.input)
        namespace.output = self._normalize_output_path(namespace.output, namespace.input)
        return namespace, unknown_args

    def _parse_headers(self, args):
        offset = 0
        header_one_is_title = self.header_one_is_title
        document_class = self.documentclass
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
        default_headers = {}
        default_headers.update({
            "headerone": (
                "title"
                if header_one_is_title
                else _DEFAULT_HEADERS[1 + offset]
            )
        })
        default_headers.update({
            f"header{_NUMBERS[i]}": _DEFAULT_HEADERS[i + offset]
            for i in range(2, 7)
        })
        parser_header.set_defaults(**default_headers)
        return parser.parse_known_args(["header"] + args)
    
    def _parse_package_args(self, args):
        namespace = parser.parse_args(["package"] + args)
        namespace = self._transform_namespace(namespace)
        namespace_dct = vars(namespace)
        used_packages = []
        used_packages.extend([pkg for pkg in packages.on_off if namespace_dct.get(f"pkg_{pkg}")])
        for functionality, _ in packages.functionality.items():
            used_packages.append(namespace_dct.get(f"pkg_{functionality}"))
        return namespace, sorted(used_packages)

    
    def _process_package_args(self, args):
        self.pkg.update({pkg: (pkg in self.packages) for pkg in packages.allowed})
        self.cmd.update({
            "single": ("emph" if "single" in self.use_emph else "textit"),
            "double": ("emph" if "double" in self.use_emph else "textbf")
        })
        self.env.update({
            "verbatim": ("Verbatim" if "fancyvrb" in self.packages else "verbatim"),
            "quote": (
                "displayquote" if "csquotes" in self.packages else
                "quoting" if "quoting" in self.packages else
                ""
                ),
        })
        self.env_args.update({
            "verbatim": (args.pkg_fancyvrb_args if "fancyvrb" in self.packages else []),
            "quote": [],
        })


    @staticmethod
    def _normalize_input_path(input_: str):
        path_in = Path(input_)
        if path_in.is_absolute():
            if path_in.exists():
                return path_in
        else:
            if path_in.absolute().exists():
                return path_in.absolute()
            if (PATH_IO / path_in).exists():
                return PATH_IO / path_in
        raise FileNotFoundError(
            f"File {input_} not found."
        )

    @staticmethod
    def _normalize_output_path(output: str, input_path: Path):
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

    @staticmethod
    def _transform_namespace(namespace, from_=None, into=None):
        if from_ is None:
            from_ = []
        if into is None:
            into = []
        from_ = _ON_OFF + from_
        into = [True, False] + into
        dct = dict(zip(from_, into))
        for key, value in vars(namespace).items():
            try:
                if value in dct:
                    setattr(namespace, key, dct[value])
            except TypeError:
                continue
        return namespace

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
