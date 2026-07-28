# Discord Username: collector668 | Roblox Username: CollectorXVIII

from typing import List
from tokens import Token
import ast_nodes as A


# A dedicated exception type allows parser failures to be distinguished from
# lexer, runtime, or general Python errors. Parser methods raise this exception
# whenever the token stream does not conform to the language grammar.
class ParseError(Exception):
    pass


class Parser:
    """
    Converts a linear sequence of lexer-generated tokens into an abstract
    syntax tree (AST).

    This parser uses recursive-descent parsing. Each method represents either a
    grammar rule or a specific operator-precedence level. The parser tracks its
    current position in the token list through `self.i` and advances only after
    confirming that the current token is valid for the expected grammar rule.
    """

    def __init__(self, tokens: List[Token]):
        # The complete token stream produced by the lexer. It is expected to
        # contain a final EOF token so that parser termination can be detected.
        self.tokens = tokens

        # Index of the token currently being examined. Keeping parsing state as
        # an index avoids removing tokens and preserves the original sequence.
        self.i = 0

    def peek(self) -> Token:
        """Return the current token without consuming it."""
        return self.tokens[self.i]

    def prev(self) -> Token:
        """
        Return the most recently consumed token.

        This is primarily used after `match` succeeds, allowing the parser to
        access the matched token's lexeme without storing a separate reference.
        """
        return self.tokens[self.i - 1]

    def at_end(self) -> bool:
        """
        Determine whether parsing has reached the explicit EOF token.

        The lexer supplies EOF as a sentinel token, which prevents parser loops
        from depending directly on the token-list length.
        """
        return self.peek().kind == "EOF"

    def advance(self) -> Token:
        """
        Consume the current token and return it.

        The index is not moved beyond EOF. After advancing, `prev()` refers to
        the token that was just consumed.
        """
        if not self.at_end():
            self.i += 1
        return self.prev()

    def check(self, kind: str, lexeme: str | None = None) -> bool:
        """
        Check the current token without consuming it.

        `kind` identifies the token category, while the optional `lexeme`
        permits exact checks for tokens that share a category. For example,
        language keywords may all use the `KW` kind but have different lexemes.
        """
        if self.at_end():
            return False

        t = self.peek()

        # A token must first match the requested structural category.
        if t.kind != kind:
            return False

        # When a lexeme is supplied, both the token kind and exact text must
        # match. Omitting the lexeme makes this a kind-only comparison.
        if lexeme is not None and t.lexeme != lexeme:
            return False

        return True

    def match(self, *kinds: str) -> bool:
        """
        Consume the current token when its kind matches any supplied kind.

        Returning a Boolean makes this suitable for grammar alternatives such
        as PLUS or MINUS without raising an error when neither is present.
        """
        if self.at_end():
            return False

        if self.peek().kind in kinds:
            self.advance()
            return True

        return False

    def match_kw(self, word: str) -> bool:
        """
        Match and consume one exact language keyword.

        Keywords share the `KW` token kind, so both the token kind and its
        lexeme must be checked to distinguish words such as `if`, `while`,
        `true`, and `end`.
        """
        if self.check("KW", word):
            self.advance()
            return True

        return False

    def consume(self, kind: str, msg: str, lexeme: str | None = None) -> Token:
        """
        Require a specific token and consume it.

        Unlike `match`, this method represents a mandatory grammar element. A
        ParseError is raised if the current token does not match, including the
        token's source line, column, kind, and lexeme for precise diagnostics.
        """
        if self.check(kind, lexeme):
            return self.advance()

        t = self.peek()
        raise ParseError(
            f"{msg} at {t.line}:{t.col} (got {t.kind}:{t.lexeme!r})"
        )

    def skip_newlines(self):
        """
        Consume consecutive newline tokens.

        Newlines separate statements and blocks in this language. This helper
        permits blank lines between valid statements without creating AST nodes.
        """
        while self.match("NEWLINE"):
            pass

    def parse(self) -> A.Program:
        """
        Parse the entire token stream and return the root Program AST node.

        Each top-level statement is parsed independently and stored in source
        order. Parsing stops only when the EOF token is reached.
        """
        stmts = []

        # Leading blank lines are ignored before parsing the first statement.
        self.skip_newlines()

        while not self.at_end():
            stmts.append(self.statement())

            # Newlines following each statement are separators rather than
            # executable syntax, so they are consumed before the next statement.
            self.skip_newlines()

        return A.Program(stmts)

    def statement(self):
        """
        Parse one complete statement.

        Statement type is selected using the leading token. Keyword-led
        statements are checked first, followed by identifier assignment
        detection. Any remaining valid input is treated as an expression
        statement.
        """

        # Variable declarations use the grammar:
        # let <identifier> = <expression>
        if self.match_kw("let"):
            name = self.consume(
                "IDENT",
                "Expected variable name"
            ).lexeme
            self.consume(
                "EQUAL",
                "Expected '=' after variable name"
            )
            expr = self.expression()
            return A.LetStmt(name, expr)

        # Control-flow statements delegate to specialised parsing methods
        # because they contain nested blocks and required closing keywords.
        if self.match_kw("if"):
            return self.if_stmt()

        if self.match_kw("while"):
            return self.while_stmt()

        if self.match_kw("repeat"):
            return self.repeat_stmt()

        # Assignment and expression statements can both begin with identifiers.
        # One-token lookahead resolves this ambiguity before consuming anything.
        if self.check("IDENT") and self._looks_like_assign():
            name = self.advance().lexeme
            self.consume("EQUAL", "Expected '=' in assignment")
            expr = self.expression()
            return A.AssignStmt(name, expr)

        # Expressions used as standalone statements are wrapped in ExprStmt so
        # the AST preserves the distinction between expressions and statements.
        expr = self.expression()
        return A.ExprStmt(expr)

    def _looks_like_assign(self) -> bool:
        """
        Use one-token lookahead to identify assignment syntax.

        An assignment must begin with an IDENT token immediately followed by an
        EQUAL token. This check does not consume either token, allowing the
        statement parser to choose the correct grammar rule safely.
        """
        if self.i + 1 >= len(self.tokens):
            return False

        t0 = self.tokens[self.i]
        t1 = self.tokens[self.i + 1]

        return t0.kind == "IDENT" and t1.kind == "EQUAL"

    def if_stmt(self):
        """
        Parse an if statement with an optional else branch.

        Expected structure:

            if <condition> then
                <then statements>
            else
                <else statements>
            end

        The caller has already consumed the initial `if` keyword.
        """
        cond = self.expression()

        # `then` marks the end of the condition and a newline marks the start
        # of the statement block.
        self.consume(
            "KW",
            "Expected 'then' after if condition",
            "then"
        )
        self.consume(
            "NEWLINE",
            "Expected newline after then"
        )

        # The first branch ends when either `else` or `end` is encountered.
        # Those terminating keywords are deliberately left unconsumed.
        then_body = self.block_until({"else", "end"})

        # The else branch is optional. None is retained when the source contains
        # no else clause, allowing the AST to represent that distinction.
        else_body = None
        if self.match_kw("else"):
            self.consume(
                "NEWLINE",
                "Expected newline after else"
            )
            else_body = self.block_until({"end"})

        # Every if statement requires one final `end`, regardless of whether an
        # else branch was present.
        self.consume(
            "KW",
            "Expected 'end' to close if",
            "end"
        )

        return A.IfStmt(cond, then_body, else_body)

    def while_stmt(self):
        """
        Parse a condition-controlled while loop.

        Expected structure:

            while <condition> do
                <body statements>
            end

        The loop condition is represented as an expression AST node, while the
        body is stored as an ordered list of statement nodes.
        """
        cond = self.expression()

        self.consume(
            "KW",
            "Expected 'do' after while condition",
            "do"
        )
        self.consume(
            "NEWLINE",
            "Expected newline after do"
        )

        body = self.block_until({"end"})

        self.consume(
            "KW",
            "Expected 'end' to close while",
            "end"
        )

        return A.WhileStmt(cond, body)

    def repeat_stmt(self):
        """
        Parse a count-controlled repeat loop.

        Expected structure:

            repeat <count expression> times
                <body statements>
            end

        The repeat count is parsed as a general expression rather than only a
        number literal, permitting variables, arithmetic, or function calls.
        """
        count_expr = self.expression()

        self.consume(
            "KW",
            "Expected 'times' after repeat count",
            "times"
        )
        self.consume(
            "NEWLINE",
            "Expected newline after times"
        )

        body = self.block_until({"end"})

        self.consume(
            "KW",
            "Expected 'end' to close repeat",
            "end"
        )

        return A.RepeatStmt(count_expr, body)

    def block_until(self, end_keywords: set[str]):
        """
        Parse statements until one of the supplied terminating keywords appears.

        The terminating keyword is not consumed here because the owning parser,
        such as `if_stmt` or `while_stmt`, must validate and consume it. This
        separation allows the same block parser to support different constructs.
        """
        stmts = []

        # Blank lines immediately inside a block are permitted.
        self.skip_newlines()

        while (
            not self.at_end()
            and not (
                self.check("KW")
                and self.peek().lexeme in end_keywords
            )
        ):
            stmts.append(self.statement())
            self.skip_newlines()

        return stmts

    # -------------------------------------------------------------------------
    # Expression parsing
    # -------------------------------------------------------------------------
    #
    # The following methods implement operator precedence through recursive
    # descent. Each method parses operators at one precedence level and delegates
    # operands to the next-higher precedence level.
    #
    # Lowest precedence:
    #   or
    #   and
    #   == !=
    #   < <= > >=
    #   + -
    #   * /
    #   unary not and unary -
    #   calls
    #   primary expressions
    # Highest precedence:
    # -------------------------------------------------------------------------

    def expression(self):
        """
        Parse a complete expression.

        `logic_or` is the entry point because logical OR has the lowest
        precedence and can therefore contain every higher-precedence expression.
        """
        return self.logic_or()

    def logic_or(self):
        """
        Parse left-associative logical OR expressions.

        Repeated operators are folded into nested Binary nodes. For example,
        `a or b or c` becomes `Binary(Binary(a, "or", b), "or", c)`.
        """
        expr = self.logic_and()

        while self.match_kw("or"):
            right = self.logic_and()
            expr = A.Binary(expr, "or", right)

        return expr

    def logic_and(self):
        """
        Parse left-associative logical AND expressions.

        Each operand is parsed through `equality`, giving equality operators
        higher precedence than logical AND.
        """
        expr = self.equality()

        while self.match_kw("and"):
            right = self.equality()
            expr = A.Binary(expr, "and", right)

        return expr

    def equality(self):
        """
        Parse equality and inequality operations.

        Both operators have equal precedence and are processed from left to
        right. Their operands are comparison expressions.
        """
        expr = self.compare()

        while True:
            if self.match("EQEQ"):
                op = "=="
            elif self.match("NOTEQ"):
                op = "!="
            else:
                break

            right = self.compare()
            expr = A.Binary(expr, op, right)

        return expr

    def compare(self):
        """
        Parse relational comparison operations.

        Comparison operators bind more tightly than equality operators but less
        tightly than arithmetic addition and subtraction.
        """
        expr = self.term()

        while True:
            if self.match("LT"):
                op = "<"
            elif self.match("LTE"):
                op = "<="
            elif self.match("GT"):
                op = ">"
            elif self.match("GTE"):
                op = ">="
            else:
                break

            right = self.term()
            expr = A.Binary(expr, op, right)

        return expr

    def term(self):
        """
        Parse addition and subtraction.

        The method name `term` represents the grammar level containing additive
        operations. Multiplication and division are delegated to `factor`, which
        gives those operations higher precedence.
        """
        expr = self.factor()

        while True:
            if self.match("PLUS"):
                op = "+"
            elif self.match("MINUS"):
                op = "-"
            else:
                break

            right = self.factor()
            expr = A.Binary(expr, op, right)

        return expr

    def factor(self):
        """
        Parse multiplication and division.

        Operands are parsed through `unary`, ensuring unary operators are applied
        before multiplicative operations.
        """
        expr = self.unary()

        while True:
            if self.match("STAR"):
                op = "*"
            elif self.match("SLASH"):
                op = "/"
            else:
                break

            right = self.unary()
            expr = A.Binary(expr, op, right)

        return expr

    def unary(self):
        """
        Parse prefix unary operators.

        Recursively calling `unary` for the operand permits chained prefix
        operators such as `not not value` or `--value`. If no unary operator is
        present, parsing proceeds to function-call syntax.
        """
        if self.match_kw("not"):
            return A.Unary("not", self.unary())

        if self.match("MINUS"):
            return A.Unary("-", self.unary())

        return self.call()

    def call(self):
        """
        Parse function-call expressions following a primary expression.

        Calls are parsed in a loop so that chained call syntax can be represented
        if the language permits a call result to be called again. Arguments are
        comma-separated expressions and may themselves contain any supported
        operator or nested function call.
        """
        expr = self.primary()

        while True:
            if self.match("LPAREN"):
                args = []

                # An immediate closing parenthesis represents an empty argument
                # list. Otherwise, at least one expression must be parsed.
                if not self.check("RPAREN"):
                    args.append(self.expression())

                    # Each comma requires another complete argument expression.
                    while self.match("COMMA"):
                        args.append(self.expression())

                self.consume(
                    "RPAREN",
                    "Expected ')' after arguments"
                )

                # The previously parsed expression becomes the callee, and the
                # collected expression nodes become its ordered arguments.
                expr = A.Call(expr, args)
                continue

            break

        return expr

    def primary(self):
        """
        Parse atomic expressions that cannot be divided into smaller operators.

        Primary expressions include literals, variable references, language
        constants, and parenthesised expressions. This is the highest-precedence
        level of the expression grammar.
        """

        # Numeric token lexemes are converted to Python numeric values before
        # being stored in the AST. A decimal point distinguishes floats from
        # integers.
        if self.match("NUMBER"):
            raw = self.prev().lexeme

            if "." in raw:
                return A.Number(float(raw))

            return A.Number(int(raw))

        # The lexer is responsible for producing the STRING token's lexeme in
        # the format expected by the AST String node.
        if self.match("STRING"):
            return A.String(self.prev().lexeme)

        # Identifiers become variable-reference nodes. Whether the variable
        # exists is a later semantic or runtime concern, not a parsing concern.
        if self.match("IDENT"):
            return A.Var(self.prev().lexeme)

        # Boolean and null values are keywords rather than generic identifiers,
        # so they are converted directly into their dedicated literal AST nodes.
        if self.match_kw("true"):
            return A.Bool(True)

        if self.match_kw("false"):
            return A.Bool(False)

        if self.match_kw("null"):
            return A.Null()

        # Parentheses override normal precedence by recursively parsing a full
        # expression before requiring the matching closing parenthesis.
        if self.match("LPAREN"):
            expr = self.expression()
            self.consume(
                "RPAREN",
                "Expected ')' after expression"
            )
            return expr

        # Reaching this point means no valid primary expression begins with the
        # current token. Source coordinates and token details make the resulting
        # parser error directly traceable to the input program.
        t = self.peek()
        raise ParseError(
            f"Expected expression at {t.line}:{t.col} "
            f"(got {t.kind}:{t.lexeme!r})"
        )
