from dataclasses import dataclass
from typing import Any, List, Optional

@dataclass
class Program:
    statements: List[Any]

# statements
@dataclass
class LetStmt:
    name: str
    value: Any

@dataclass
class AssignStmt:
    name: str
    value: Any

@dataclass
class ExprStmt:
    expr: Any

@dataclass
class IfStmt:
    cond: Any
    then_body: List[Any]
    else_body: Optional[List[Any]] = None

@dataclass
class WhileStmt:
    cond: Any
    body: List[Any]

@dataclass
class RepeatStmt:
    count: Any
    body: List[Any]

# expressions
@dataclass
class Number:
    value: float | int

@dataclass
class String:
    value: str

@dataclass
class Bool:
    value: bool

@dataclass
class Null:
    value: None = None

@dataclass
class Var:
    name: str

@dataclass
class Unary:
    op: str
    right: Any

@dataclass
class Binary:
    left: Any
    op: str
    right: Any

@dataclass
class Call:
    callee: Any
    args: List[Any]

def dump(node, indent=0):
    pad = "  " * indent
    t = type(node).__name__

    if isinstance(node, Program):
        out = [f"{pad}{t}("]
        for s in node.statements:
            out.append(dump(s, indent + 1))
        out.append(f"{pad})")
        return "\n".join(out)

    if isinstance(node, (LetStmt, AssignStmt)):
        return f"{pad}{t}(name={node.name!r}, value=\n{dump(node.value, indent+1)})"

    if isinstance(node, ExprStmt):
        return f"{pad}{t}(\n{dump(node.expr, indent+1)}\n{pad})"

    if isinstance(node, IfStmt):
        out = [f"{pad}{t}("]
        out.append(f"{pad}  cond=")
        out.append(dump(node.cond, indent + 2))
        out.append(f"{pad}  then=[")
        for s in node.then_body:
            out.append(dump(s, indent + 2))
        out.append(f"{pad}  ]")
        if node.else_body is not None:
            out.append(f"{pad}  else=[")
            for s in node.else_body:
                out.append(dump(s, indent + 2))
            out.append(f"{pad}  ]")
        out.append(f"{pad})")
        return "\n".join(out)

    if isinstance(node, WhileStmt):
        out = [f"{pad}{t}("]
        out.append(f"{pad}  cond=")
        out.append(dump(node.cond, indent + 2))
        out.append(f"{pad}  body=[")
        for s in node.body:
            out.append(dump(s, indent + 2))
        out.append(f"{pad}  ]")
        out.append(f"{pad})")
        return "\n".join(out)

    if isinstance(node, RepeatStmt):
        out = [f"{pad}{t}("]
        out.append(f"{pad}  count=")
        out.append(dump(node.count, indent + 2))
        out.append(f"{pad}  body=[")
        for s in node.body:
            out.append(dump(s, indent + 2))
        out.append(f"{pad}  ]")
        out.append(f"{pad})")
        return "\n".join(out)

    if isinstance(node, (Number, String, Bool, Null, Var)):
        if isinstance(node, Null):
            return f"{pad}{t}()"
        if isinstance(node, Var):
            return f"{pad}{t}({node.name!r})"
        return f"{pad}{t}({node.value!r})"

    if isinstance(node, Unary):
        return f"{pad}{t}(op={node.op!r}, right=\n{dump(node.right, indent+1)})"

    if isinstance(node, Binary):
        return (
            f"{pad}{t}(\n"
            f"{dump(node.left, indent+1)}\n"
            f"{pad}  op={node.op!r}\n"
            f"{dump(node.right, indent+1)}\n"
            f"{pad})"
        )

    if isinstance(node, Call):
        out = [f"{pad}{t}("]
        out.append(dump(node.callee, indent + 1))
        out.append(f"{pad}  args=[")
        for a in node.args:
            out.append(dump(a, indent + 2))
        out.append(f"{pad}  ]")
        out.append(f"{pad})")
        return "\n".join(out)

    return f"{pad}{t}({node!r})"
