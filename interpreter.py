# Discord Username: collector668 | Roblox Username: CollectorXVIII
"""AST interpreter for the educational programming language."""

import ast_nodes as A


MAX_LOOP_ITERATIONS = 200_000


class RuntimeErrorKid(Exception):
    """Raised for errors caused by the interpreted program."""


class Env:
    """
    Store variables for one scope and optionally link to an enclosing scope.

    The current language runs in a global scope, but the parent link keeps
    lookup and assignment ready for future function or local-scope support.
    """

    def __init__(self, parent=None):
        self.parent = parent
        self.values = {}

    def define(self, name, value) -> None:
        """Create or replace a value in the current scope."""
        self.values[name] = value

    def assign(self, name, value) -> None:
        """Update the nearest existing definition of a variable."""
        if name in self.values:
            self.values[name] = value
            return

        if self.parent is not None:
            self.parent.assign(name, value)
            return

        raise RuntimeErrorKid(self._hint_undefined(name))

    def get(self, name):
        """Retrieve a variable from the nearest scope containing it."""
        if name in self.values:
            return self.values[name]

        if self.parent is not None:
            return self.parent.get(name)

        raise RuntimeErrorKid(self._hint_undefined(name))

    @staticmethod
    def _hint_undefined(name: str) -> str:
        return (
            f"You used '{name}' before creating it.\n"
            f"Fix: write `let {name} = ...` first, "
            f"then use `{name}` later."
        )


def _truthy(value) -> bool:
    """Apply the language's truth-value rules."""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value != ""
    return True


def _number(value):
    """Return a numeric value or raise a language-level type error."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return value

    raise RuntimeErrorKid(
        f"Expected a number, but got {type(value).__name__}."
    )


def _whole_number(value, context: str) -> int:
    """
    Validate values used as counts.

    Silently truncating 2.8 to 2 would hide mistakes, so non-integral floating
    point values are rejected rather than converted.
    """
    number = _number(value)

    if isinstance(number, float) and not number.is_integer():
        raise RuntimeErrorKid(
            f"{context} needs a whole number, but got {number}."
        )

    return int(number)


def _is_builtin(value) -> bool:
    """Check the tagged tuple representation used for built-in functions."""
    return (
        isinstance(value, tuple)
        and len(value) == 2
        and value[0] == "builtin"
        and callable(value[1])
    )


class Interpreter:
    """Execute Program, statement and expression nodes produced by the parser."""

    def __init__(self, step: bool = False):
        self.env = Env()
        self.step = step
        self._install_builtins()

    def _install_builtins(self) -> None:
        """Register the language functions available before user code runs."""

        def say(*args):
            output = " ".join(
                self._stringify(argument)
                for argument in args
            )
            print(output)
            return None

        def ask(prompt=""):
            if prompt is None:
                prompt = ""
            elif not isinstance(prompt, str):
                prompt = self._stringify(prompt)

            return input(prompt)

        # A tag distinguishes callable built-ins from ordinary runtime values.
        self.env.define("say", ("builtin", say))
        self.env.define("ask", ("builtin", ask))

    def _stringify(self, value) -> str:
        """Convert internal values to the language's display format."""
        if value is None:
            return "null"
        if value is True:
            return "true"
        if value is False:
            return "false"
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)

    def run(self, program: A.Program) -> None:
        """Execute all top-level statements in source order."""
        for statement in program.statements:
            self._step(statement)
            self.exec_stmt(statement)

    def _step(self, statement) -> None:
        """Pause before a statement when interactive step mode is enabled."""
        if not self.step:
            return

        print("\n--- STEP ---")

        try:
            print(A.dump(statement))
        except Exception:
            print(statement)

        print("vars:", self._env_snapshot())
        input("Press Enter to run this step...")

    def _env_snapshot(self) -> str:
        """Return the currently visible variables for step-mode diagnostics."""
        scopes = []
        current = self.env

        while current is not None:
            scopes.append(current.values)
            current = current.parent

        visible = {}
        for scope in reversed(scopes):
            visible.update(scope)

        items = []
        for name, value in visible.items():
            if _is_builtin(value):
                items.append(f"{name}=<builtin>")
            else:
                items.append(
                    f"{name}={self._stringify(value)}"
                )

        return "{ " + ", ".join(items) + " }"

    def exec_block(self, statements) -> None:
        """Execute every statement in a control-flow body."""
        for statement in statements:
            self._step(statement)
            self.exec_stmt(statement)

    def exec_stmt(self, statement):
        """Dispatch one statement node to its runtime behaviour."""
        if isinstance(statement, A.LetStmt):
            value = self.eval_expr(statement.value)
            self.env.define(statement.name, value)
            return None

        if isinstance(statement, A.AssignStmt):
            value = self.eval_expr(statement.value)
            self.env.assign(statement.name, value)
            return None

        if isinstance(statement, A.ExprStmt):
            return self.eval_expr(statement.expr)

        if isinstance(statement, A.IfStmt):
            condition = self.eval_expr(statement.cond)

            if _truthy(condition):
                self.exec_block(statement.then_body)
            elif statement.else_body is not None:
                self.exec_block(statement.else_body)

            return None

        if isinstance(statement, A.WhileStmt):
            iterations = 0

            while _truthy(
                self.eval_expr(statement.cond)
            ):
                if iterations >= MAX_LOOP_ITERATIONS:
                    raise RuntimeErrorKid(
                        "This loop looks infinite.\n"
                        "Fix: make sure something changes "
                        "inside the loop so it can stop."
                    )

                self.exec_block(statement.body)
                iterations += 1

            return None

        if isinstance(statement, A.RepeatStmt):
            count_value = self.eval_expr(statement.count)
            count = _whole_number(count_value, "repeat")

            if count < 0:
                raise RuntimeErrorKid(
                    "repeat needs a positive number (0 or more)."
                )

            if count > MAX_LOOP_ITERATIONS:
                raise RuntimeErrorKid(
                    "repeat number is too big for safety."
                )

            for _ in range(count):
                self.exec_block(statement.body)

            return None

        raise RuntimeErrorKid(
            f"Unknown statement: {type(statement).__name__}"
        )

    def eval_expr(self, expression):
        """Evaluate one expression node and return its runtime value."""
        if isinstance(expression, A.Number):
            return expression.value

        if isinstance(expression, A.String):
            return expression.value

        if isinstance(expression, A.Bool):
            return expression.value

        if isinstance(expression, A.Null):
            return None

        if isinstance(expression, A.Var):
            return self.env.get(expression.name)

        if isinstance(expression, A.Unary):
            right = self.eval_expr(expression.right)

            if expression.op == "-":
                return -_number(right)

            if expression.op == "not":
                return not _truthy(right)

            raise RuntimeErrorKid(
                f"Unknown operator {expression.op!r}"
            )

        if isinstance(expression, A.Binary):
            return self._eval_binary(expression)

        if isinstance(expression, A.Call):
            return self._eval_call(expression)

        raise RuntimeErrorKid(
            f"Unknown expression: {type(expression).__name__}"
        )

    def _eval_binary(self, expression: A.Binary):
        """
        Evaluate a binary expression.

        Logical operators are handled before the right operand is evaluated so
        they preserve short-circuit behaviour.
        """
        left = self.eval_expr(expression.left)

        if expression.op == "and":
            if not _truthy(left):
                return left
            return self.eval_expr(expression.right)

        if expression.op == "or":
            if _truthy(left):
                return left
            return self.eval_expr(expression.right)

        right = self.eval_expr(expression.right)

        if expression.op == "+":
            if isinstance(left, str) or isinstance(right, str):
                return (
                    self._stringify(left)
                    + self._stringify(right)
                )
            return _number(left) + _number(right)

        if expression.op == "-":
            return _number(left) - _number(right)

        if expression.op == "*":
            if isinstance(left, str):
                count = _whole_number(
                    right,
                    "String repetition",
                )
                if count < 0:
                    raise RuntimeErrorKid(
                        "String repetition cannot be negative."
                    )
                return left * count

            if isinstance(right, str):
                count = _whole_number(
                    left,
                    "String repetition",
                )
                if count < 0:
                    raise RuntimeErrorKid(
                        "String repetition cannot be negative."
                    )
                return right * count

            return _number(left) * _number(right)

        if expression.op == "/":
            divisor = _number(right)

            if divisor == 0:
                raise RuntimeErrorKid(
                    "Division by zero.\n"
                    "Fix: do not divide by 0."
                )

            return _number(left) / divisor

        if expression.op == "==":
            return left == right

        if expression.op == "!=":
            return left != right

        if expression.op == "<":
            return _number(left) < _number(right)

        if expression.op == "<=":
            return _number(left) <= _number(right)

        if expression.op == ">":
            return _number(left) > _number(right)

        if expression.op == ">=":
            return _number(left) >= _number(right)

        raise RuntimeErrorKid(
            f"Unknown operator {expression.op!r}"
        )

    def _eval_call(self, expression: A.Call):
        """Evaluate the callee and arguments, then invoke a built-in function."""
        callee = self.eval_expr(expression.callee)
        arguments = [
            self.eval_expr(argument)
            for argument in expression.args
        ]

        if not _is_builtin(callee):
            raise RuntimeErrorKid(
                "You tried to call something that is not a function.\n"
                "Fix: call built-ins like say(...) or ask(...)."
            )

        function = callee[1]

        try:
            return function(*arguments)
        except TypeError as error:
            raise RuntimeErrorKid(
                f"Invalid arguments for built-in function: {error}"
            ) from error
