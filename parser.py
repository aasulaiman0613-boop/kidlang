from typing import List
from tokens import Token
import ast_nodes as A

class ParseError(Exception):
    pass

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.i = 0

    def peek(self) -> Token:
        return self.tokens[self.i]

    def prev(self) -> Token:
        return self.tokens[self.i - 1]

    def at_end(self) -> bool:
        return self.peek().kind == "EOF"

    def advance(self) -> Token:
        if not self.at_end():
            self.i += 1
        return self.prev()

    def check(self, kind: str, lexeme: str | None = None) -> bool:
        if self.at_end():
            return False
        t = self.peek()
        if t.kind != kind:
            return False
        if lexeme is not None and t.lexeme != lexeme:
            return False
        return True

    def match(self, *kinds: str) -> bool:
        if self.at_end():
            return False
        if self.peek().kind in kinds:
            self.advance()
            return True
        return False

    def match_kw(self, word: str) -> bool:
        if self.check("KW", word):
            self.advance()
            return True
        return False

    def consume(self, kind: str, msg: str, lexeme: str | None = None) -> Token:
        if self.check(kind, lexeme):
            return self.advance()
        t = self.peek()
        raise ParseError(f"{msg} at {t.line}:{t.col} (got {t.kind}:{t.lexeme!r})")

    def skip_newlines(self):
        while self.match("NEWLINE"):
            pass

    def parse(self) -> A.Program:
        stmts = []
        self.skip_newlines()
        while not self.at_end():
            stmts.append(self.statement())
            self.skip_newlines()
        return A.Program(stmts)

    def statement(self):
        if self.match_kw("let"):
            name = self.consume("IDENT", "Expected variable name").lexeme
            self.consume("EQUAL", "Expected '=' after variable name")
            expr = self.expression()
            return A.LetStmt(name, expr)

        if self.match_kw("if"):
            return self.if_stmt()

        if self.match_kw("while"):
            return self.while_stmt()

        if self.match_kw("repeat"):
            return self.repeat_stmt()

        if self.check("IDENT") and self._looks_like_assign():
            name = self.advance().lexeme
            self.consume("EQUAL", "Expected '=' in assignment")
            expr = self.expression()
            return A.AssignStmt(name, expr)

        expr = self.expression()
        return A.ExprStmt(expr)

    def _looks_like_assign(self) -> bool:
        if self.i + 1 >= len(self.tokens):
            return False
        t0 = self.tokens[self.i]
        t1 = self.tokens[self.i + 1]
        return t0.kind == "IDENT" and t1.kind == "EQUAL"

    def if_stmt(self):
        cond = self.expression()
        self.consume("KW", "Expected 'then' after if condition", "then")
        self.consume("NEWLINE", "Expected newline after then")

        then_body = self.block_until({"else", "end"})

        else_body = None
        if self.match_kw("else"):
            self.consume("NEWLINE", "Expected newline after else")
            else_body = self.block_until({"end"})

        self.consume("KW", "Expected 'end' to close if", "end")
        return A.IfStmt(cond, then_body, else_body)

    def while_stmt(self):
        cond = self.expression()
        self.consume("KW", "Expected 'do' after while condition", "do")
        self.consume("NEWLINE", "Expected newline after do")
        body = self.block_until({"end"})
        self.consume("KW", "Expected 'end' to close while", "end")
        return A.WhileStmt(cond, body)

    def repeat_stmt(self):
        count_expr = self.expression()
        self.consume("KW", "Expected 'times' after repeat count", "times")
        self.consume("NEWLINE", "Expected newline after times")
        body = self.block_until({"end"})
        self.consume("KW", "Expected 'end' to close repeat", "end")
        return A.RepeatStmt(count_expr, body)

    def block_until(self, end_keywords: set[str]):
        stmts = []
        self.skip_newlines()
        while not self.at_end() and not (self.check("KW") and self.peek().lexeme in end_keywords):
            stmts.append(self.statement())
            self.skip_newlines()
        return stmts

    # expressions
    def expression(self):
        return self.logic_or()

    def logic_or(self):
        expr = self.logic_and()
        while self.match_kw("or"):
            right = self.logic_and()
            expr = A.Binary(expr, "or", right)
        return expr

    def logic_and(self):
        expr = self.equality()
        while self.match_kw("and"):
            right = self.equality()
            expr = A.Binary(expr, "and", right)
        return expr

    def equality(self):
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
        if self.match_kw("not"):
            return A.Unary("not", self.unary())
        if self.match("MINUS"):
            return A.Unary("-", self.unary())
        return self.call()

    def call(self):
        expr = self.primary()
        while True:
            if self.match("LPAREN"):
                args = []
                if not self.check("RPAREN"):
                    args.append(self.expression())
                    while self.match("COMMA"):
                        args.append(self.expression())
                self.consume("RPAREN", "Expected ')' after arguments")
                expr = A.Call(expr, args)
                continue
            break
        return expr

    def primary(self):
        if self.match("NUMBER"):
            raw = self.prev().lexeme
            if "." in raw:
                return A.Number(float(raw))
            return A.Number(int(raw))

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
            expr = self.expression()
            self.consume("RPAREN", "Expected ')' after expression")
            return expr

        t = self.peek()
        raise ParseError(f"Expected expression at {t.line}:{t.col} (got {t.kind}:{t.lexeme!r})")

