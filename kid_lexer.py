from tokens import Token

KEYWORDS = {
    "let","if","then","else","end","while","do","fun","return",
    "true","false","null","and","or","not",
    "repeat","times",
}

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

DOUBLE = {
    "==": "EQEQ",
    "!=": "NOTEQ",
    "<=": "LTE",
    ">=": "GTE",
}

SINGLE2 = {
    "<": "LT",
    ">": "GT",
}

def lex(src: str):
    tokens = []
    i = 0
    line = 1
    col = 1

    def push(kind, lexeme, ln, cl):
        tokens.append(Token(kind, lexeme, ln, cl))

    while i < len(src):
        ch = src[i]

        if ch in " \t\r":
            i += 1
            col += 1
            continue

        if ch == "\n":
            push("NEWLINE", "\n", line, col)
            i += 1
            line += 1
            col = 1
            continue

        if ch == "#":
            while i < len(src) and src[i] != "\n":
                i += 1
            continue
        if ch == "-" and i + 1 < len(src) and src[i+1] == "-":
            i += 2
            while i < len(src) and src[i] != "\n":
                i += 1
            continue

        if i + 1 < len(src):
            two = src[i:i+2]
            if two in DOUBLE:
                push(DOUBLE[two], two, line, col)
                i += 2
                col += 2
                continue

        if ch in SINGLE:
            push(SINGLE[ch], ch, line, col)
            i += 1
            col += 1
            continue
        if ch in SINGLE2:
            push(SINGLE2[ch], ch, line, col)
            i += 1
            col += 1
            continue

        if ch == '"':
            ln, cl = line, col
            i += 1
            col += 1
            out = []
            while i < len(src) and src[i] != '"':
                if src[i] == "\\" and i + 1 < len(src):
                    nxt = src[i+1]
                    if nxt == "n":
                        out.append("\n")
                        i += 2
                        col += 2
                        continue
                    if nxt == "t":
                        out.append("\t")
                        i += 2
                        col += 2
                        continue
                    out.append(nxt)
                    i += 2
                    col += 2
                    continue
                if src[i] == "\n":
                    raise SyntaxError(f"Unterminated string at {ln}:{cl}")
                out.append(src[i])
                i += 1
                col += 1
            if i >= len(src) or src[i] != '"':
                raise SyntaxError(f"Unterminated string at {ln}:{cl}")
            i += 1
            col += 1
            push("STRING", "".join(out), ln, cl)
            continue

        if ch.isdigit():
            ln, cl = line, col
            j = i
            dot = 0
            while j < len(src) and (src[j].isdigit() or src[j] == "."):
                if src[j] == ".":
                    dot += 1
                    if dot > 1:
                        break
                j += 1
            lexeme = src[i:j]
            push("NUMBER", lexeme, ln, cl)
            col += (j - i)
            i = j
            continue

        if ch.isalpha() or ch == "_":
            ln, cl = line, col
            j = i
            while j < len(src) and (src[j].isalnum() or src[j] == "_"):
                j += 1
            word = src[i:j]
            if word in KEYWORDS:
                push("KW", word, ln, cl)
            else:
                push("IDENT", word, ln, cl)
            col += (j - i)
            i = j
            continue

        raise SyntaxError(f"Unexpected character {ch!r} at {line}:{col}")

    push("EOF", "", line, col)
    return tokens
