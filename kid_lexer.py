# Discord Username: collector668 | Roblox Username: CollectorXVIII
"""Lexer for a small educational programming language."""

from tokens import Token


KEYWORDS = {
    "let",
    "if",
    "then",
    "else",
    "end",
    "while",
    "do",
    "true",
    "false",
    "null",
    "and",
    "or",
    "not",
    "repeat",
    "times",
}

SINGLE_CHAR_TOKENS = {
    "(": "LPAREN",
    ")": "RPAREN",
    ",": "COMMA",
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "/": "SLASH",
    "=": "EQUAL",
    "<": "LT",
    ">": "GT",
}

DOUBLE_CHAR_TOKENS = {
    "==": "EQEQ",
    "!=": "NOTEQ",
    "<=": "LTE",
    ">=": "GTE",
}

ESCAPES = {
    "n": "\n",
    "t": "\t",
    '"': '"',
    "\\": "\\",
}


def lex(src: str) -> list[Token]:
    """
    Convert source text into tokens while preserving source positions.

    Newlines are emitted because the parser uses them to separate statements
    and block headers. Spaces and comments are ignored.
    """
    tokens: list[Token] = []
    i = 0
    line = 1
    col = 1

    def push(kind: str, lexeme: str, token_line: int, token_col: int) -> None:
        tokens.append(Token(kind, lexeme, token_line, token_col))

    while i < len(src):
        ch = src[i]

        # Horizontal whitespace has no syntactic meaning.
        if ch in " \t\r":
            i += 1
            col += 1
            continue

        # Newlines remain visible to the parser.
        if ch == "\n":
            push("NEWLINE", "\n", line, col)
            i += 1
            line += 1
            col = 1
            continue

        # The language accepts both # comments and -- comments.
        if ch == "#":
            while i < len(src) and src[i] != "\n":
                i += 1
                col += 1
            continue

        if ch == "-" and i + 1 < len(src) and src[i + 1] == "-":
            i += 2
            col += 2
            while i < len(src) and src[i] != "\n":
                i += 1
                col += 1
            continue

        # Longest-match handling prevents <= from becoming LT + EQUAL.
        if i + 1 < len(src):
            pair = src[i : i + 2]
            if pair in DOUBLE_CHAR_TOKENS:
                push(DOUBLE_CHAR_TOKENS[pair], pair, line, col)
                i += 2
                col += 2
                continue

        if ch in SINGLE_CHAR_TOKENS:
            push(SINGLE_CHAR_TOKENS[ch], ch, line, col)
            i += 1
            col += 1
            continue

        if ch == '"':
            start_line = line
            start_col = col
            i += 1
            col += 1
            chars: list[str] = []

            while i < len(src) and src[i] != '"':
                if src[i] == "\n":
                    raise SyntaxError(
                        f"Unterminated string at {start_line}:{start_col}"
                    )

                if src[i] == "\\":
                    if i + 1 >= len(src):
                        raise SyntaxError(
                            f"Unterminated string at {start_line}:{start_col}"
                        )

                    escaped = src[i + 1]
                    if escaped not in ESCAPES:
                        raise SyntaxError(
                            f"Unknown escape sequence \\{escaped} "
                            f"at {line}:{col}"
                        )

                    chars.append(ESCAPES[escaped])
                    i += 2
                    col += 2
                    continue

                chars.append(src[i])
                i += 1
                col += 1

            if i >= len(src):
                raise SyntaxError(
                    f"Unterminated string at {start_line}:{start_col}"
                )

            i += 1
            col += 1
            push("STRING", "".join(chars), start_line, start_col)
            continue

        if ch.isdigit():
            start = i
            start_line = line
            start_col = col

            while i < len(src) and src[i].isdigit():
                i += 1
                col += 1

            if i < len(src) and src[i] == ".":
                if i + 1 >= len(src) or not src[i + 1].isdigit():
                    raise SyntaxError(
                        f"Malformed number at {start_line}:{start_col}"
                    )

                i += 1
                col += 1

                while i < len(src) and src[i].isdigit():
                    i += 1
                    col += 1

                if i < len(src) and src[i] == ".":
                    raise SyntaxError(
                        f"Malformed number at {start_line}:{start_col}"
                    )

            push("NUMBER", src[start:i], start_line, start_col)
            continue

        if ch.isalpha() or ch == "_":
            start = i
            start_line = line
            start_col = col

            while i < len(src) and (
                src[i].isalnum() or src[i] == "_"
            ):
                i += 1
                col += 1

            word = src[start:i]
            kind = "KW" if word in KEYWORDS else "IDENT"
            push(kind, word, start_line, start_col)
            continue

        raise SyntaxError(
            f"Unexpected character {ch!r} at {line}:{col}"
        )

    # EOF is a sentinel that lets the parser stop safely.
    push("EOF", "", line, col)
    return tokens
