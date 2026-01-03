from pathlib import Path

from src.compiler import Compiler

PROGRAM_PATH = Path().resolve() / "examples" / "example4" / "main.ehir"


def main():
    compiler = Compiler()
    compiler.compile(PROGRAM_PATH)


if __name__ == "__main__":
    main()
