# Discord Username: collector668 | Roblox Username: CollectorXVIII

# Import the abstract syntax tree node definitions used by the interpreter.
# The parser creates these nodes, and this module executes them.
import ast_nodes as A


# A custom runtime exception separates errors caused by the interpreted
# language from ordinary Python exceptions raised by the interpreter itself.
class RuntimeErrorKid(Exception):
    pass


# Env represents a variable scope. Each environment stores its own variables
# and may reference a parent environment for enclosing-scope lookups.
class Env:
    def __init__(self, parent=None):
        # The parent is searched when a variable is not present locally.
        # A value of None indicates that this is the global environment.
        self.parent = parent

        # Variable names are mapped to their runtime values in this dictionary.
        self.values = {}

    def define(self, name, value):
        # Creating a variable always writes directly into the current scope.
        # Existing values with the same name in this scope are overwritten.
        self.values[name] = value

    def assign(self, name, value):
        # Assignment first checks the current scope. This ensures that the
        # nearest existing variable is updated.
        if name in self.values:
            self.values[name] = value
            return

        # If the variable is not local, recursively search the enclosing scope.
        # This supports assignments to variables defined outside a nested scope.
        if self.parent is not None:
            self.parent.assign(name, value)
            return

        # Reaching the root environment without finding the name means that the
        # program attempted to assign to a variable that was never declared.
        raise RuntimeErrorKid(self._hint_undefined(name))

    def get(self, name):
        # Variable lookup begins in the current scope.
        if name in self.values:
            return self.values[name]

        # If the variable is not local, recursively search parent environments.
        if self.parent is not None:
            return self.parent.get(name)

        # A failed search through every scope produces a user-oriented error.
        raise RuntimeErrorKid(self._hint_undefined(name))

    def _hint_undefined(self, name):
        # Construct an instructional error message that identifies the missing
        # variable and explains how it should be declared before use.
        return (
            f"You used '{name}' before creating it.\n"
            f"Fix: write `let {name} = ...` first, then use `{name}` later."
        )


# Convert a runtime value into the language's Boolean interpretation.
# This centralises truth-value behaviour for conditionals, loops and `not`.
def _truthy(v):
    # The language treats null as false.
    if v is None:
        return False

    # Boolean values retain their existing truth value.
    if isinstance(v, bool):
        return v

    # Zero is false, while every non-zero integer or floating-point value is true.
    if isinstance(v, (int, float)):
        return v != 0

    # Empty strings are false, while strings containing characters are true.
    if isinstance(v, str):
        return v != ""

    # Any additional runtime object type is considered true by default.
    return True


# Validate and convert a runtime value for numeric operations.
def _num(v):
    # Python treats bool as a subclass of int. This explicit branch converts
    # true and false into 1 and 0 intentionally before the broader number check.
    if isinstance(v, bool):
        return int(v)

    # Integers and floating-point values are already valid numeric operands.
    if isinstance(v, (int, float)):
        return v

    # Arithmetic with any other value type is rejected with a readable error.
    raise RuntimeErrorKid(f"Expected a number, but got {type(v).__name__}.")


# Interpreter walks the AST produced by the parser and performs each operation.
# Statements control execution and state, while expressions calculate values.
class Interpreter:
    def __init__(self, step=False):
        # The interpreter begins with one global environment. It contains both
        # user-created variables and the built-in functions installed below.
        self.env = Env()

        # Step mode optionally pauses before executing each statement, allowing
        # the current AST node and variable state to be inspected interactively.
        self.step = step

        # Built-ins must be registered before user code begins execution.
        self._install_builtins()

    def _install_builtins(self):
        # `say` is the language's output function. It accepts any number of
        # arguments, converts each one using language-specific formatting and
        # prints the resulting space-separated text.
        def say(*args):
            out = " ".join(self._stringify(a) for a in args)
            print(out)

            # Output functions do not produce a meaningful value, so the
            # language-level result is null, represented internally by None.
            return None

        # `ask` displays an optional prompt and returns text entered by the user.
        def ask(prompt=""):
            # A null prompt is converted to an empty prompt.
            if prompt is None:
                prompt = ""

            # Non-string prompts are converted using the same formatting rules
            # used by `say`, maintaining consistent language output.
            if not isinstance(prompt, str):
                prompt = self._stringify(prompt)

            return input(prompt)

        # Built-in functions are represented by tagged tuples. The "builtin"
        # marker lets call evaluation distinguish callable language functions
        # from ordinary tuples or values.
        self.env.define("say", ("builtin", say))
        self.env.define("ask", ("builtin", ask))

    def _stringify(self, v):
        # Convert Python's internal None value into the language keyword `null`.
        if v is None:
            return "null"

        # Booleans use lowercase language literals instead of Python's
        # capitalised True and False representations.
        if v is True:
            return "true"

        if v is False:
            return "false"

        # A floating-point value with no fractional component is displayed as
        # an integer. For example, 5.0 is displayed as 5.
        if isinstance(v, float) and v.is_integer():
            return str(int(v))

        # Other values use their normal string representation.
        return str(v)

    def run(self, program: A.Program):
        # Execute top-level statements in the same order they appeared in the
        # source program.
        try:
            for stmt in program.statements:
                # Step inspection occurs immediately before statement execution.
                self._step(stmt)
                self.exec_stmt(stmt)

        # Runtime errors are re-raised as the same custom error type, preserving
        # a consistent public error interface for callers of the interpreter.
        except RuntimeErrorKid as e:
            raise RuntimeErrorKid(str(e))

    def _step(self, stmt):
        # When step mode is disabled, execution continues without interruption.
        if not self.step:
            return

        print("\n--- STEP ---")

        try:
            # Prefer the AST module's structured representation because it
            # exposes the statement's internal tree more clearly.
            print(A.dump(stmt))
        except Exception:
            # Fall back to the object's standard representation if AST dumping
            # is unavailable or fails for this particular node.
            print(stmt)

        # Display the current global environment before running the statement.
        print("vars:", self._env_snapshot())

        # Pausing here allows the user to inspect state one statement at a time.
        input("Press Enter to run this step...")

    def _env_snapshot(self):
        # Build a shallow, human-readable view of the current environment.
        # Parent environments are not traversed by this diagnostic helper.
        items = []

        for k, v in self.env.values.items():
            # Built-in implementation functions should not be exposed directly,
            # so they are represented with a descriptive placeholder.
            if isinstance(v, tuple) and len(v) == 2 and v[0] == "builtin":
                items.append(f"{k}=<builtin>")
            else:
                # Ordinary values use the interpreter's display formatting.
                items.append(f"{k}={self._stringify(v)}")

        return "{ " + ", ".join(items) + " }"

    def exec_block(self, statements):
        # Execute every statement in a block sequentially. This helper is shared
        # by conditional branches and loop bodies.
        for s in statements:
            self._step(s)
            self.exec_stmt(s)

    def exec_stmt(self, stmt):
        # A LetStmt evaluates its initializer and creates a variable in the
        # current environment.
        if isinstance(stmt, A.LetStmt):
            val = self.eval_expr(stmt.value)
            self.env.define(stmt.name, val)
            return None

        # An AssignStmt evaluates its new value and updates the nearest existing
        # variable with the matching name.
        if isinstance(stmt, A.AssignStmt):
            val = self.eval_expr(stmt.value)
            self.env.assign(stmt.name, val)
            return None

        # An expression statement is evaluated for its side effects or result.
        # A common example is calling `say(...)`.
        if isinstance(stmt, A.ExprStmt):
            return self.eval_expr(stmt.expr)

        # An IfStmt evaluates its condition once and executes exactly one branch.
        if isinstance(stmt, A.IfStmt):
            cond = self.eval_expr(stmt.cond)

            if _truthy(cond):
                self.exec_block(stmt.then_body)
            else:
                # The parser represents a missing else branch with None.
                if stmt.else_body is not None:
                    self.exec_block(stmt.else_body)

            return None

        # A WhileStmt repeatedly evaluates its condition before each iteration.
        if isinstance(stmt, A.WhileStmt):
            # The guard limits the number of iterations to protect the host
            # process from simple accidental infinite loops.
            guard = 0

            while _truthy(self.eval_expr(stmt.cond)):
                self.exec_block(stmt.body)
                guard += 1

                # More than 200,000 iterations is treated as a likely infinite
                # loop and stopped with an instructional runtime error.
                if guard > 200000:
                    raise RuntimeErrorKid(
                        "This loop looks infinite.\n"
                        "Fix: make sure something changes inside the loop so it can stop."
                    )

            return None

        # A RepeatStmt executes its body a fixed number of times.
        if isinstance(stmt, A.RepeatStmt):
            # The count can be any expression, so it must be evaluated first.
            n = self.eval_expr(stmt.count)

            # Repeat counts must be numeric. Boolean values are converted by
            # `_num` according to the language's numeric conversion rules.
            n = _num(n)

            # The runtime uses an integer iteration count. Floating-point values
            # are truncated by Python's int conversion.
            n_int = int(n)

            # Negative iteration counts are invalid because repetition can only
            # occur zero or more times.
            if n_int < 0:
                raise RuntimeErrorKid(
                    "repeat needs a positive number (0 or more)."
                )

            # The upper limit prevents extremely large loops from consuming
            # excessive execution time.
            if n_int > 200000:
                raise RuntimeErrorKid("repeat number is too big for safety.")

            for _ in range(n_int):
                self.exec_block(stmt.body)

            return None

        # Reaching this point means the AST contains a statement type that this
        # interpreter does not recognise or support.
        raise RuntimeErrorKid(
            f"Unknown statement: {type(stmt).__name__}"
        )

    def eval_expr(self, expr):
        # Literal AST nodes directly return their stored runtime values.
        if isinstance(expr, A.Number):
            return expr.value

        if isinstance(expr, A.String):
            return expr.value

        if isinstance(expr, A.Bool):
            return expr.value

        # The language's null literal is represented internally by Python None.
        if isinstance(expr, A.Null):
            return None

        # Variable expressions retrieve values through the environment's scoped
        # lookup process.
        if isinstance(expr, A.Var):
            return self.env.get(expr.name)

        # Unary expressions evaluate one operand before applying their operator.
        if isinstance(expr, A.Unary):
            right = self.eval_expr(expr.right)

            # Unary minus requires a numeric operand and returns its negation.
            if expr.op == "-":
                return -_num(right)

            # Logical not uses the language's custom truth-value rules.
            if expr.op == "not":
                return not _truthy(right)

            # Any other unary operator indicates an unsupported or malformed AST.
            raise RuntimeErrorKid(f"Unknown operator {expr.op!r}")

        # Binary expressions combine a left operand, an operator and a right
        # operand. Evaluation order normally proceeds from left to right.
        if isinstance(expr, A.Binary):
            left = self.eval_expr(expr.left)

            # Logical AND uses short-circuit evaluation. The right side is only
            # evaluated when the left side is truthy.
            if expr.op == "and":
                return (
                    self.eval_expr(expr.right)
                    if _truthy(left)
                    else left
                )

            # Logical OR also short-circuits. A truthy left value is returned
            # without evaluating the right expression.
            if expr.op == "or":
                return (
                    left
                    if _truthy(left)
                    else self.eval_expr(expr.right)
                )

            # All remaining binary operators require both operands, so the right
            # expression is evaluated after short-circuit cases are handled.
            right = self.eval_expr(expr.right)

            # Addition performs string concatenation when either operand is a
            # string. Otherwise, both operands must be numeric.
            if expr.op == "+":
                if isinstance(left, str) or isinstance(right, str):
                    return (
                        self._stringify(left)
                        + self._stringify(right)
                    )

                return _num(left) + _num(right)

            # Subtraction accepts numeric values only.
            if expr.op == "-":
                return _num(left) - _num(right)

            # Multiplication supports both numeric multiplication and string
            # repetition when exactly one operand is a string and the other is
            # an integer or floating-point value.
            if expr.op == "*":
                if (
                    isinstance(left, str)
                    and isinstance(right, (int, float))
                ):
                    return left * int(_num(right))

                if (
                    isinstance(right, str)
                    and isinstance(left, (int, float))
                ):
                    return right * int(_num(left))

                return _num(left) * _num(right)

            # Division validates the divisor separately so that division by zero
            # produces a clear language-level error instead of a Python error.
            if expr.op == "/":
                r = _num(right)

                if r == 0:
                    raise RuntimeErrorKid(
                        "Division by zero.\n"
                        "Fix: do not divide by 0."
                    )

                return _num(left) / r

            # Equality operators compare values directly using Python's equality
            # semantics for the runtime types stored by the language.
            if expr.op == "==":
                return left == right

            if expr.op == "!=":
                return left != right

            # Relational comparisons require numeric operands and therefore pass
            # both values through the numeric validator.
            if expr.op == "<":
                return _num(left) < _num(right)

            if expr.op == "<=":
                return _num(left) <= _num(right)

            if expr.op == ">":
                return _num(left) > _num(right)

            if expr.op == ">=":
                return _num(left) >= _num(right)

            # An unknown operator indicates that the AST and interpreter support
            # different operator sets.
            raise RuntimeErrorKid(f"Unknown operator {expr.op!r}")

        # Call expressions evaluate the callable target and every argument before
        # determining whether the target is a supported language function.
        if isinstance(expr, A.Call):
            callee = self.eval_expr(expr.callee)

            # Arguments are evaluated from left to right and collected in their
            # original source order.
            args = [self.eval_expr(a) for a in expr.args]

            # Built-in functions use a two-item tuple whose first value is the
            # "builtin" tag and whose second value is the Python implementation.
            if (
                isinstance(callee, tuple)
                and len(callee) == 2
                and callee[0] == "builtin"
            ):
                fn = callee[1]
                return fn(*args)

            # Ordinary values cannot be called as functions.
            raise RuntimeErrorKid(
                "You tried to call something that is not a function.\n"
                "Fix: call built-ins like say(...) or ask(...)."
            )

        # This final fallback detects expression node types that the interpreter
        # does not currently support.
        raise RuntimeErrorKid(
            f"Unknown expression: {type(expr).__name__}"
        )
