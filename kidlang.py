import sys, os, pathlib
sys.path.insert(0, os.path.dirname(__file__))

from kid_lexer import lex
from parser import Parser, ParseError
from interpreter import Interpreter, RuntimeErrorKid

def main():
    # Run: python kidlang.py
    # Step mode: python kidlang.py --step
    step = "--step" in sys.argv

    path = pathlib.Path("tests/main.kid")
    if len(sys.argv) >= 2 and sys.argv[1] not in ("--step",):
        path = pathlib.Path(sys.argv[1])

    src = path.read_text(encoding="utf-8")

    tokens = lex(src)
    program = Parser(tokens).parse()

    try:
        Interpreter(step=step).run(program)
    except (RuntimeErrorKid, ParseError) as e:
        print("\nERROR:")
        print(e)

if __name__ == "__main__":
    main()
