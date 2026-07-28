# Discord Username: collector668 | Roblox Username: CollectorXVIII
"""Recursive-descent parser for the educational language."""

from typing import List

import ast_nodes as A
from tokens import Token


class ParseError(Exception):
    """Raised when a valid token sequence does not match the grammar."""


class Parser:
    """
    Convert lexer tokens into an abstract syntax tree.

    Each expression method represents one precedence level. Lower-precedence
    methods call higher-precedence methods, which produces the intended tree
    structure without a separate precedence table.
    """

    def __init__(self, tokens: List[Token]):
        if not tokens:
            raise ValueError("Parser requires a token stream containing EOF.")

        self.tokens = tokens
        self.i = 0

    def peek(self) -> Token:
        """Return the current token without consuming it."""
        return self.tokens[self.i]

    def prev(self) -> Token:
        """Return the most recently consumed token."""
        return self.tokens[self.i - 1]

    def at_end(self) -> bool:
        """Check whether the current token is the EOF sentinel."""
        return self.peek().kind == "EOF"

    def advance(self) -> Token:
        """Consume and return the current token."""
        current = self.peek()
        if not self.at_end():
            self.i += 1
        return current

    def check(self, kind: str, lexeme: str | None = None) -> bool:
        """Check the current token's kind and optional exact lexeme."""
        if self.at_end():
            return False

        token = self.peek()
        if token.kind != kind:
            return False
        if lexeme is not None and token.lexeme != lexeme:
            return False
        return True

    def match(self, *kinds: str) -> bool:
        """Consume the current token if its kind matches any supplied kind."""
        if self.at_end():
            return False

        if self.peek().kind in kinds:
            self.advance()
            return True
        return False

    def match_kw(self, word: str) -> bool:
        """Consume one exact keyword."""
        if self.check("KW", word):
            self.advance()
            return True
        return False

    def consume(
        self,
        kind: str,
        message: str,
        lexeme: str | None = None,
    ) -> Token:
        """Require a token or raise a source-positioned parse error."""
        if self.check(kind, lexeme):
            return self.advance()

        token = self.peek()
        raise ParseError(
            f"{message} at {token.line}:{token.col} "
            f"(got {token.kind}:{token.lexeme!r})"
        )

    def skip_newlines(self) -> None:
        """Allow blank lines between statements."""
        while self.match("NEWLINE"):
            pass

    def parse(self) -> A.Program:
        """Parse the complete token stream into a Program node."""
        statements = []
        self.skip_newlines()

        while not self.at_end():
            if self.check("KW") and self.peek().lexeme in {"else", "end"}:
                token = self.peek()
                raise ParseError(
                    f"Unexpected {token.lexeme!r} at "
                    f"{token.line}:{token.col}"
                )

            statements.append(self.statement())
            self.skip_newlines()

        return A.Program(statements)

    def statement(self):
        """Select and parse one statement from its leading token."""
        if self.match_kw("let"):
            name = self.consume(
                "IDENT",
                "Expected variable name after 'let'",
            ).lexeme
            self.consume(
                "EQUAL",
                "Expected '=' after variable name",
            )
            return A.LetStmt(name, self.expression())

        if self.match_kw("if"):
            return self.if_stmt()

        if self.match_kw("while"):
            return self.while_stmt()

        if self.match_kw("repeat"):
            return self.repeat_stmt()

        # Assignment and variable expressions both begin with IDENT, so one
        # token of lookahead resolves the ambiguity without consuming input.
        if self.check("IDENT") and self._looks_like_assign():
            name = self.advance().lexeme
            self.consume("EQUAL", "Expected '=' in assignment")
            return A.AssignStmt(name, self.expression())

        return A.ExprStmt(self.expression())

    def _looks_like_assign(self) -> bool:
        """Return True when IDENT is immediately followed by EQUAL."""
        if self.i + 1 >= len(self.tokens):
            return False

        current = self.tokens[self.i]
        following = self.tokens[self.i + 1]
        return (
            current.kind == "IDENT"
            and following.kind == "EQUAL"
        )

    def if_stmt(self):
        """
        Parse an if/else/end structure.

        The initial 'if' keyword has already been consumed by statement().
        """
        condition = self.expression()
        self.consume(
            "KW",
            "Expected 'then' after if condition",
            "then",
        )
        self.consume(
            "NEWLINE",
            "Expected newline after 'then'",
        )

        then_body = self.block_until({"else", "end"})
        else_body = None

        if self.match_kw("else"):
            self.consume(
                "NEWLINE",
                "Expected newline after 'else'",
            )
            else_body = self.block_until({"end"})

        self.consume(
            "KW",
            "Expected 'end' to close if statement",
            "end",
        )
        return A.IfStmt(condition, then_body, else_body)

    def while_stmt(self):
        """Parse a condition-controlled while loop."""
        condition = self.expression()
        self.consume(
            "KW",
            "Expected 'do' after while condition",
            "do",
        )
        self.consume(
            "NEWLINE",
            "Expected newline after 'do'",
        )

        body = self.block_until({"end"})
        self.consume(
            "KW",
            "Expected 'end' to close while loop",
            "end",
        )
        return A.WhileStmt(condition, body)

    def repeat_stmt(self):
        """Parse a count-controlled repeat loop."""
        count = self.expression()
        self.consume(
            "KW",
            "Expected 'times' after repeat count",
            "times",
        )
        self.consume(
            "NEWLINE",
            "Expected newline after 'times'",
        )

        body = self.block_until({"end"})
        self.consume(
            "KW",
            "Expected 'end' to close repeat loop",
            "end",
        )
        return A.RepeatStmt(count, body)

    def block_until(self, end_keywords: set[str]):
        """
        Parse statements until a matching block terminator is reached.

        The terminator is left unconsumed so the owning statement parser can
        validate whether 'else' or 'end' is legal in that position.
        """
        statements = []
        self.skip_newlines()

        while not self.at_end():
            if (
                self.check("KW")
                and self.peek().lexeme in end_keywords
            ):
                break

            statements.append(self.statement())
            self.skip_newlines()

        return statements

    # Expression grammar, ordered from lowest to highest precedence.

    def expression(self):
        return self.logic_or()

    def logic_or(self):
        expression = self.logic_and()

        while self.match_kw("or"):
            right = self.logic_and()
            expression = A.Binary(expression, "or", right)

        return expression

    def logic_and(self):
        expression = self.equality()

        while self.match_kw("and"):
            right = self.equality()
            expression = A.Binary(expression, "and", right)

        return expression

    def equality(self):
        expression = self.compare()

        while True:
            if self.match("EQEQ"):
                operator = "=="
            elif self.match("NOTEQ"):
                operator = "!="
            else:
                break

            right = self.compare()
            expression = A.Binary(expression, operator, right)

        return expression

    def compare(self):
        expression = self.term()

        while True:
            if self.match("LT"):
                operator = "<"
            elif self.match("LTE"):
                operator = "<="
            elif self.match("GT"):
                operator = ">"
            elif self.match("GTE"):
                operator = ">="
            else:
                break

            right = self.term()
            expression = A.Binary(expression, operator, right)

        return expression

    def term(self):
        expression = self.factor()

        while True:
            if self.match("PLUS"):
                operator = "+"
            elif self.match("MINUS"):
                operator = "-"
            else:
                break

            right = self.factor()
            expression = A.Binary(expression, operator, right)

        return expression

    def factor(self):
        expression = self.unary()

        while True:
            if self.match("STAR"):
                operator = "*"
            elif self.match("SLASH"):
                operator = "/"
            else:
                break

            right = self.unary()
            expression = A.Binary(expression, operator, right)

        return expression

    def unary(self):
        # Recursion allows chained prefixes such as not not value or --value.
        if self.match_kw("not"):
            return A.Unary("not", self.unary())

        if self.match("MINUS"):
            return A.Unary("-", self.unary())

        return self.call()

    def call(self):
        """Parse a primary expression followed by zero or more call suffixes."""
        expression = self.primary()

        while self.match("LPAREN"):
            arguments = []

            if not self.check("RPAREN"):
                arguments.append(self.expression())

                while self.match("COMMA"):
                    arguments.append(self.expression())

            self.consume(
                "RPAREN",
                "Expected ')' after arguments",
            )
            expression = A.Call(expression, arguments)

        return expression

    def primary(self):
        """Parse literals, variables, constants and grouped expressions."""
        if self.match("NUMBER"):
            raw = self.prev().lexeme
            value = float(raw) if "." in raw else int(raw)
            return A.Number(value)

        if self.match("STRING"):
            return A.String(self.prev().lexeme)

        if self.match("IDENT"):
            return A.Var(self.prev().lexeme)

        if self.match_kw("true"):
            return A.Bool(True)

        if self.match_kw("false"):
            return A.Bool(False)

        if self.match_kw("null"):
            return A.Null()

        if self.match("LPAREN"):
            expression = self.expression()
            self.consume(
                "RPAREN",
                "Expected ')' after expression",
            )
            return expression

        token = self.peek()
        raise ParseError(
            f"Expected expression at {token.line}:{token.col} "
            f"(got {token.kind}:{token.lexeme!r})"
        )
