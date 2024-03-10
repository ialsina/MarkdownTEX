from re import compile, DOTALL, MULTILINE

headerone = compile(r"^#{1}\s*(.+)\s*$", MULTILINE)
headertwo = compile(r"^#{2}\s*(.+)\s*$", MULTILINE)
headerthree = compile(r"^#{3}\s*(.+)\s*$", MULTILINE)
headerfour = compile(r"^#{4}\s*(.+)\s*$", MULTILINE)
headerfive = compile(r"^#{5}\s*(.+)\s*$", MULTILINE)
headersix = compile(r"^#{6}\s*(.+)\s*$", MULTILINE)
headerany = compile(r"^#+\s*(.+)\s*$", MULTILINE)

inline_code = compile(r"(?<![`\\])`([^`]+?)(?<!\\)`(?!`)")
block_code = compile(r"^```(.*?)\n(.*?)\n```$", MULTILINE+DOTALL)
block_quotes = compile(r"\n((^>+.*\n)+)", MULTILINE)

href = compile(r"\[(.+?)\]\((.+?)\)")

environment = compile(
    r"\[//\]:\s(?:<>|#)\s\(%texenv begin (.*)\)(.+?)\[//\]:\s(?:<>|#)\s\(%texenv end \1\)",
    DOTALL+MULTILINE
)

list_dash = compile(r"\n(-\s*.*?\n)+\n", MULTILINE)
list_ast = compile(r"\n(\*\s*.*?\n)+\n", MULTILINE)
list_plus = compile(r"\n(\+\s*.*?\n)+\n", MULTILINE)
list_num = compile(r"\n(\d+\.\s*.*?\n)+\n", MULTILINE)

emph_3ast = compile(r"(?<!\*)\*{3}(\w[^\*\n]*?\w)\*{3}(?!\*)",)
emph_3usc = compile(r"(?<!_)_{3}(\w[^\_\n]*?\w)_{3}(?!_)")
emph_2ast = compile(r"(?<!\*)\*{2}(\w[^\*\n]*?\w)\*{2}(?!\*)",)
emph_2usc = compile(r"(?<!_)_{2}(\w[^\_\n]*?\w)_{2}(?!_)",)
emph_1ast = compile(r"(?<!\*)\*{1}(\w[^\*\n]*?\w)\*{1}(?!\*)",)
emph_1usc = compile(r"(?<!_)_{1}(\w[^\*\n]*?\w)_{1}(?!_)",)

comment = compile(r"\[//\]:\s+(?:<>|#)\s+\((.*)\)")
comment_cmd = compile(r"% (\w*)\s*(.*)")
