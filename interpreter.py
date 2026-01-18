import ast_nodes as A

class RuntimeErrorKid(Exception):
    pass

class Env:
    def __init__(self, parent=None):
        self.parent = parent
        self.values = {}

    def define(self, name, value):
        self.values[name] = value

    def assign(self, name, value):
        if name in self.values:
            self.values[name] = value
            return
        if self.parent is not None:
            self.parent.assign(name, value)
            return
        raise RuntimeErrorKid(self._hint_undefined(name))

    def get(self, name):
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.get(name)
        raise RuntimeErrorKid(self._hint_undefined(name))

    def _hint_undefined(self, name):
        return (
            f"You used '{name}' before creating it.\n"
            f"Fix: write `let {name} = ...` first, then use `{name}` later."
        )

def _truthy(v):
    if v is None:
        return False
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, str):
        return v != ""
    return True

def _num(v):
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)):
        return v
    raise RuntimeErrorKid(f"Expected a number, but got {type(v).__name__}.")

class Interpreter:
    def __init__(self, step=False):
        self.env = Env()
        self.step = step
        self._install_builtins()

    def _install_builtins(self):
        def say(*args):
            out = " ".join(self._stringify(a) for a in args)
            print(out)
            return None

        def ask(prompt=""):
            if prompt is None:
                prompt = ""
            if not isinstance(prompt, str):
                prompt = self._stringify(prompt)
            return input(prompt)

        self.env.define("say", ("builtin", say))
        self.env.define("ask", ("builtin", ask))

    def _stringify(self, v):
        if v is None:
            return "null"
        if v is True:
            return "true"
        if v is False:
            return "false"
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v)

    def run(self, program: A.Program):
        try:
            for stmt in program.statements:
                self._step(stmt)
                self.exec_stmt(stmt)
        except RuntimeErrorKid as e:
            raise RuntimeErrorKid(str(e))

    def _step(self, stmt):
        if not self.step:
            return
        print("\n--- STEP ---")
        try:
            print(A.dump(stmt))
        except Exception:
            print(stmt)
        print("vars:", self._env_snapshot())
        input("Press Enter to run this step...")

    def _env_snapshot(self):
        # shallow view of current env (kid-friendly)
        items = []
        for k, v in self.env.values.items():
            if isinstance(v, tuple) and len(v) == 2 and v[0] == "builtin":
                items.append(f"{k}=<builtin>")
            else:
                items.append(f"{k}={self._stringify(v)}")
        return "{ " + ", ".join(items) + " }"

    def exec_block(self, statements):
        for s in statements:
            self._step(s)
            self.exec_stmt(s)

    def exec_stmt(self, stmt):
        if isinstance(stmt, A.LetStmt):
            val = self.eval_expr(stmt.value)
            self.env.define(stmt.name, val)
            return None

        if isinstance(stmt, A.AssignStmt):
            val = self.eval_expr(stmt.value)
            self.env.assign(stmt.name, val)
            return None

        if isinstance(stmt, A.ExprStmt):
            return self.eval_expr(stmt.expr)

        if isinstance(stmt, A.IfStmt):
            cond = self.eval_expr(stmt.cond)
            if _truthy(cond):
                self.exec_block(stmt.then_body)
            else:
                if stmt.else_body is not None:
                    self.exec_block(stmt.else_body)
            return None

        if isinstance(stmt, A.WhileStmt):
            guard = 0
            while _truthy(self.eval_expr(stmt.cond)):
                self.exec_block(stmt.body)
                guard += 1
                if guard > 200000:
                    raise RuntimeErrorKid(
                        "This loop looks infinite.\n"
                        "Fix: make sure something changes inside the loop so it can stop."
                    )
            return None

        if isinstance(stmt, A.RepeatStmt):
            n = self.eval_expr(stmt.count)
            n = _num(n)
            n_int = int(n)
            if n_int < 0:
                raise RuntimeErrorKid("repeat needs a positive number (0 or more).")
            if n_int > 200000:
                raise RuntimeErrorKid("repeat number is too big for safety.")
            for _ in range(n_int):
                self.exec_block(stmt.body)
            return None

        raise RuntimeErrorKid(f"Unknown statement: {type(stmt).__name__}")

    def eval_expr(self, expr):
        if isinstance(expr, A.Number):
            return expr.value
        if isinstance(expr, A.String):
            return expr.value
        if isinstance(expr, A.Bool):
            return expr.value
        if isinstance(expr, A.Null):
            return None
        if isinstance(expr, A.Var):
            return self.env.get(expr.name)

        if isinstance(expr, A.Unary):
            right = self.eval_expr(expr.right)
            if expr.op == "-":
                return -_num(right)
            if expr.op == "not":
                return not _truthy(right)
            raise RuntimeErrorKid(f"Unknown operator {expr.op!r}")

        if isinstance(expr, A.Binary):
            left = self.eval_expr(expr.left)

            if expr.op == "and":
                return self.eval_expr(expr.right) if _truthy(left) else left
            if expr.op == "or":
                return left if _truthy(left) else self.eval_expr(expr.right)

            right = self.eval_expr(expr.right)

            if expr.op == "+":
                if isinstance(left, str) or isinstance(right, str):
                    return self._stringify(left) + self._stringify(right)
                return _num(left) + _num(right)

            if expr.op == "-":
                return _num(left) - _num(right)

            if expr.op == "*":
                if isinstance(left, str) and isinstance(right, (int, float)):
                    return left * int(_num(right))
                if isinstance(right, str) and isinstance(left, (int, float)):
                    return right * int(_num(left))
                return _num(left) * _num(right)

            if expr.op == "/":
                r = _num(right)
                if r == 0:
                    raise RuntimeErrorKid("Division by zero.\nFix: do not divide by 0.")
                return _num(left) / r

            if expr.op == "==":
                return left == right
            if expr.op == "!=":
                return left != right
            if expr.op == "<":
                return _num(left) < _num(right)
            if expr.op == "<=":
                return _num(left) <= _num(right)
            if expr.op == ">":
                return _num(left) > _num(right)
            if expr.op == ">=":
                return _num(left) >= _num(right)

            raise RuntimeErrorKid(f"Unknown operator {expr.op!r}")

        if isinstance(expr, A.Call):
            callee = self.eval_expr(expr.callee)
            args = [self.eval_expr(a) for a in expr.args]

            if isinstance(callee, tuple) and len(callee) == 2 and callee[0] == "builtin":
                fn = callee[1]
                return fn(*args)

            raise RuntimeErrorKid(
                "You tried to call something that is not a function.\n"
                "Fix: call built-ins like say(...) or ask(...)."
            )

        raise RuntimeErrorKid(f"Unknown expression: {type(expr).__name__}")
