# Markdown test document

[//]: # This is a comment and is therefore ignored.

## Heading level 2

In LaTeX, a heading level 2 is translated as a `chapter`.

### Heading level 3

In LaTeX, a heading level 3 is translated as a `section`.

#### Heading level 4

In LaTeX, a heading level 4 is translated as a `subsection`.

##### Heading level 5

To be decided.

###### Heading level 6

To be decided.


This is a Paragraph.

This is another paragraph.

This is a paragraph  
featuring a line break.

In Markdown, bold text can be rendedred using **double asterisks** or __underscores__. In turn, italics can be rendered using *single asterisks* or _underscores_. ***Triple asterisks*** or ___underscores___ renders bold, italic text.

> Blockquotes are created with the symbol >

> Blockquotes
> can be spanned
> through multiple lines.

> In addition, blockquotes
> 
>> can be nested.
> 
> Keep in mind that they need a blank line before and after.

Ordered lists are created using numbers
1. Item number one
2. Item number two
3. Item number three
1. Item number four

And unordered lists can be created using dashes (-):
- Item number one
- Item number two
- Item number three
- Item number four

Alternatively, asterisks (\*) can be used:
* Item number one
* Item number two
* Item number three
* Item number four

Finally, plus signs (+) can additionally be used:
+ Item number one
+ Item number two
+ Item number three
+ Item number four

However, combinations of such symbols are not allowed.

Single `items of code` can be enclosed in backticks (\`). This is also useful for paths, and become a `texttt` (teletype text) statement in LaTeX.

```
Blocks of code can be added
either with a block enclosed
in triple backticks
```

    or, alternatively, in a text
    indented with at least 4 spaces
    or 1 tab.

```Preliminary annotation
A block of code enclosed in
triple backticks can incorporate a
prelimiary annotation, which can have 
different usages.
```

Markdown [links](https://en.wikipedia.org/wiki/Hyperlink) are also supported and wrapped around a LaTeX [`href`](https://en.wikibooks.org/wiki/LaTeX/Hyperlinks) statement.