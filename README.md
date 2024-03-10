# MarkdownTEX

MarkdownTEX is a Python package intended to convert a Markdown document into a LaTeX document.

## Installation

To install it, clone it from Github or your own fork, create a dedicated virtual environment and install it from source.

```
git clone git@github.com:ialsina/MarkdownTEX.git
cd MarkdownTEX
python -m venv .venv
source .venv/bin/activate
pip install .
```

Note that you will need a version of Python 3.10 or superior.

## Usage

Once the package is installed mdtex, the command

```
md2tex input_file.md
```

will translate `input_file.md` into LaTeX.

### Command-line options

The following options can be passed:

  - `--help` (or `-h`)
  - `--output [OUTPUT]` (or `-o`)
  - `--title TITLE [TITLE]` (or `-T`)
  - `--author [AUTHOR]` (or `-A`)
  - `--date [DATE]` (or `-D`)
  - `--documentclass {book,report,article}` (or `-d`)
  - `--header-one-is-title {ON,OFF}` (or `-1`)
  - `--header{one,two,three,four,five,six} [HEADER]`
  - `--escape [ESCAPE_CHARACTERS]` (or `-e`)
  - `--latex-symb {ON,OFF}` (or `-L`)
  - `--use-emph [{single,double}]`
  - `--break-ligatures {ON,OFF}` (or `-H`)
  - `--pkg-<PACKAGE> {ON,OFF}`
  - `--pkg-<FUNCTIONALITY> [PACKAGE]`
  - `--pkg-<PACKAGE>-args [PACKAGE_ARGS]`
  - `--verbose` (or `-v`)

#### `output`

If a file name is passed, that will be the output file name. By default, the input file name (with the `.tex` extension) is used.
If a directory is passed, that will be the output file directory. By default the current working directory is used.
If a full path (absolute or relative to the current working directory) is passed, that will be the output directory and file name.

#### `documentclass`

The LaTeX `documentclass` to use. The supported document classes are `book`, `report` or `article`. That affects mainly how the Markdown header tags (`#`, `##`, `###`, ...) translate into LaTeX.

Roughly, 

- With `book`, the LaTeX header order reads `part`, `chapter`, `section`, `subsection`, `subsubsection`, ...
- With `report`, the LaTeX header order reads `chapter`, `section`, `subsection`, `subsubsection`, `paragraph`, ...
- With `article`, the LaTeX header order reads `section`, `subsection`, `subsubsection`, `paragraph`, `subparagraph`, ...

This behavior can be altered with the options `--header-one-is-title` and `--header{one,two,three,four,five,six}` (see below).

#### `title`, `author`, `date`

The LaTeX tags for title, author and date can be passed via command line by means of these options.

#### `header-one-is-title`

If `--header-one-is-title ON` is passed, then the Markdown main header tag (`#`) becomes the LaTeX `title` tag. Then, the subsequent Markdown header tags become the LaTeX headers, sequentially, as described above. If `--header-one-is-title OFF` is passed, then the Markdown main header tag (`#`) does not have a special effect in the LaTeX header tag sequence.

The default behavior of this feature can be set in `defaults.yaml`.

#### `headerone`, `headertwo`, `headerthree`...

The `N`-th Markdown header tag can be manually set to a custom LaTeX header tag by passing one of the following options:

1. `--headerone [HEADER]`
2. `--headertwo [HEADER]`
3. `--headerthree [HEADER]`
4. `--headerfour [HEADER]`
5. `--headerfive [HEADER]`
6. `--headersix [HEADER]`

#### `escape`

Escaping a character typesetting it with a leading backslash (\) in LaTeX. Characters such as "$", "%", "_", or the backslash itself, "\" need to be escaped in LaTeX so that it is properly interpretted as a character, not a command. To pass a custom list of characters to escape, pass `--escape %#@\`. A default list of escaped characters can also be found in `defaults.yaml`.

#### `latex-symb`

Set this option to `ON` or `OFF` to enable or disable the rendering of the LaTeX symbol.

#### `use-emph`

Usually, a single leading and trailing underscore (or asterisk) renders text in italic. This is translated to the `\textit` command in LaTeX. Similarly, a double leading and trailing underscore (or asterisk) renders text in bold. This is translated to the `\textbf` command in LaTeX.

Passing the option `--use-emph single` will enable the usage of the alternative command `\emph` instead of `\textit`. Likewise, passing the option `--use-emph double` will enable the usage of the same command instead of `\textbf`.

#### `break-hyphen-ligatures`

LaTeX 

#### Package customization

The term *package* refers to LaTeX packages. Depending on the nature of the package, there are two ways to configure package usage.

1. When there is a choice on whether a package can be used or not, the option `--pkg-<PACKAGE>` can be passed with the argument `ON` or `OFF`.
2. When the choice is among a number of packages for a given functionality, the option `--pkg-<FUNCTIONALITY> [PACKAGE]` must be used, where "`<FUNCTIONALITY>`" represents a keyword that selects a functionality, and "`<PACKAGE>`" represents a package name.

Two examples would be

1. `--pkg-fancyvrb ON`, to use the package `fancyvrb`, or `--pkg-fancyvrb OFF` to not use it
2. `--pkg-quotes csquotes` to use the package `csquotes` *to represent the quotes in the document*, or `--pkg-quotes quoting` to use the package `quoting` instead *to that end*.

In both cases, an argument `--pkg-<PACKAGE>-args` can be passed along with package-related arguments. This depends heavily on the nature and usage of the package and can be arguments to be passed in the LaTeX `\usepackage` statement, or in the environment itself.

To see a relation of allowed packages, functionalities and arguments, run

```md2tex-packages```

in the terminal.

### In-document commands

(Under construction)
