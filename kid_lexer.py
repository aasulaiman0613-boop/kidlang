# Discord Username: collector668 | Roblox Username: CollectorXVIII

# Token is the data structure used to represent one recognised piece of source
# code. Each token records its category, original value, line and column.
from tokens import Token


# Reserved words are recognised separately from ordinary identifiers.
# All entries in this set are emitted with the shared token kind "KW".
# The parser later checks the keyword's lexeme to distinguish their meanings.
KEYWORDS = {
    "let","if","then","else","end","while","do","fun","return",
    "true","false","null","and","or","not",
    "repeat","times",
}


# SINGLE maps one-character symbols to their corresponding token kinds.
# Dictionary lookup allows the lexer to recognise these symbols without using
# a separate conditional branch for every operator or punctuation character.
SINGLE = {
    "(": "LPAREN",
    ")": "RPAREN",
    ",": "COMMA",
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "/": "SLASH",
    "=": "EQUAL",
}


# DOUBLE contains operators that consist of exactly two characters.
# These must be checked before the one-character operators so that, for
# example, "==" is not incorrectly emitted as two separate EQUAL tokens.
DOUBLE = {
    "==": "EQEQ",
    "!=": "NOTEQ",
    "<=": "LTE",
    ">=": "GTE",
}


# The remaining single-character comparison operators are stored separately.
# They are tested after DOUBLE so "<=" and ">=" retain their intended meaning.
SINGLE2 = {
    "<": "LT",
    ">": "GT",
}


def lex(src: str):
    """
    Convert source-code text into an ordered sequence of Token objects.

    The lexer scans the source from left to right while tracking the current
    character index, line number and column number. Each recognised language
    element is converted into a token for the parser. Whitespace and comments
    are ignored, while newline characters are retained because this language
    uses them to separate statements and begin blocks.
    """

    # Tokens are appended in source order and returned after the scan finishes.
    tokens = []

    # `i` is the absolute character index within the complete source string.
    i = 0

    # Source positions begin at line 1, column 1 for readable diagnostics.
    line = 1
    col = 1

    def push(kind, lexeme, ln, cl):
        """
        Append a token using its type, value and starting source position.

        The starting line and column are passed explicitly because scanning a
        multi-character token changes the current lexer position before the
        completed token is appended.
        """
        tokens.append(Token(kind, lexeme, ln, cl))

    # Continue scanning until every character in the source has been processed.
    while i < len(src):
        # Read the current source character without advancing the lexer.
        ch = src[i]

        # Spaces, tabs and carriage returns have no syntactic meaning in this
        # language. They are skipped while their column width is still counted.
        if ch in " \t\r":
            i += 1
            col += 1
            continue

        # Newlines are significant because the parser expects them between
        # statements and after block-opening keywords such as `then` and `do`.
        if ch == "\n":
            push("NEWLINE", "\n", line, col)
            i += 1

            # Entering a new line increments the line number and resets the
            # column position to the first character.
            line += 1
            col = 1
            continue

        # A hash character begins a single-line comment. Every character until
        # the following newline is ignored. The newline itself is deliberately
        # left unconsumed so the normal newline branch can emit a NEWLINE token.
        if ch == "#":
            while i < len(src) and src[i] != "\n":
                i += 1
            continue

        # Two hyphens provide an alternative single-line comment syntax.
        # Checking the next character ensures an individual minus symbol still
        # remains available as an arithmetic or unary operator.
        if ch == "-" and i + 1 < len(src) and src[i+1] == "-":
            i += 2

            # As with hash comments, scanning stops before the newline so that
            # statement separation remains visible to the parser.
            while i < len(src) and src[i] != "\n":
                i += 1
            continue

        # Two-character operators are checked before single-character symbols.
        # This applies maximal matching: the longest valid operator beginning at
        # the current position is selected.
        if i + 1 < len(src):
            two = src[i:i+2]

            if two in DOUBLE:
                push(DOUBLE[two], two, line, col)
                i += 2
                col += 2
                continue

        # Recognise punctuation and arithmetic operators containing one
        # character. The dictionary supplies the correct token kind.
        if ch in SINGLE:
            push(SINGLE[ch], ch, line, col)
            i += 1
            col += 1
            continue

        # Recognise the remaining one-character comparison operators.
        # Their two-character forms have already been handled above.
        if ch in SINGLE2:
            push(SINGLE2[ch], ch, line, col)
            i += 1
            col += 1
            continue

        # A double quote begins a string literal.
        if ch == '"':
            # Preserve the opening quote's position for both the final token and
            # any unterminated-string error message.
            ln, cl = line, col

            # Consume the opening quotation mark.
            i += 1
            col += 1

            # Decoded string characters are collected here. The stored token
            # value excludes the surrounding quotation marks.
            out = []

            # Continue until a closing quote is encountered or input ends.
            while i < len(src) and src[i] != '"':
                # A backslash introduces an escape sequence when another
                # character is available after it.
                if src[i] == "\\" and i + 1 < len(src):
                    nxt = src[i+1]

                    # The two-character sequence \n becomes an actual newline
                    # character within the stored string value.
                    if nxt == "n":
                        out.append("\n")
                        i += 2
                        col += 2
                        continue

                    # The two-character sequence \t becomes a tab character.
                    if nxt == "t":
                        out.append("\t")
                        i += 2
                        col += 2
                        continue

                    # Any other escaped character is inserted directly. This
                    # supports escaped quotes, backslashes and similar values.
                    out.append(nxt)
                    i += 2
                    col += 2
                    continue

                # Raw source newlines are not permitted inside string literals.
                # The error points to the position of the opening quotation mark.
                if src[i] == "\n":
                    raise SyntaxError(f"Unterminated string at {ln}:{cl}")

                # Ordinary characters are appended unchanged.
                out.append(src[i])
                i += 1
                col += 1

            # Reaching the end of the source without a closing quote means the
            # string was never terminated.
            if i >= len(src) or src[i] != '"':
                raise SyntaxError(f"Unterminated string at {ln}:{cl}")

            # Consume the closing quotation mark.
            i += 1
            col += 1

            # Join all decoded characters and emit one STRING token whose
            # position refers to the original opening quote.
            push("STRING", "".join(out), ln, cl)
            continue

        # A digit begins a numeric literal.
        if ch.isdigit():
            # Save the number's starting position before scanning its contents.
            ln, cl = line, col

            # `j` advances independently so the complete token can be sliced
            # from the original source after its endpoint is known.
            j = i

            # Track decimal points so a numeric token contains no more than one.
            dot = 0

            # Accept consecutive digits and at most one decimal point.
            while j < len(src) and (src[j].isdigit() or src[j] == "."):
                if src[j] == ".":
                    dot += 1

                    # A second decimal point ends the current number rather than
                    # allowing an invalid multi-decimal numeric token.
                    if dot > 1:
                        break

                j += 1

            # Preserve the number as source text. Conversion to int or float is
            # performed later by the parser when it creates the AST node.
            lexeme = src[i:j]
            push("NUMBER", lexeme, ln, cl)

            # Move both the absolute index and column by the number of consumed
            # characters.
            col += (j - i)
            i = j
            continue

        # Identifiers may begin with an alphabetic character or underscore.
        if ch.isalpha() or ch == "_":
            # Save the identifier's starting source position.
            ln, cl = line, col
            j = i

            # After the first character, identifiers may contain letters,
            # digits or underscores.
            while j < len(src) and (src[j].isalnum() or src[j] == "_"):
                j += 1

            # Extract the complete identifier or keyword text.
            word = src[i:j]

            # Reserved words use the common KW token kind. All other valid names
            # become IDENT tokens for variables and callable references.
            if word in KEYWORDS:
                push("KW", word, ln, cl)
            else:
                push("IDENT", word, ln, cl)

            # Advance past the complete word.
            col += (j - i)
            i = j
            continue

        # Any character that reaches this branch does not belong to the
        # language's recognised whitespace, comments, literals, identifiers,
        # punctuation or operators.
        raise SyntaxError(f"Unexpected character {ch!r} at {line}:{col}")

    # EOF is a sentinel token used by the parser to detect the end of input
    # safely without repeatedly comparing its index against the token-list size.
    push("EOF", "", line, col)

    return tokens
