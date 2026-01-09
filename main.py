from argparse import ArgumentParser
from pathlib import Path

from ehir.compiler import Compiler


def main():
    parser = ArgumentParser(prog="ehir", description="EHIR Compiler")
    parser.add_argument("input_file", help="Path to the input file")
    args = parser.parse_args()

    program_path = Path(args.input_file)
    if not program_path.is_absolute():
        program_path = Path().resolve() / program_path

    if not program_path.exists():
        print(f"Error: File '{program_path}' does not exist.")
        exit(-1)

    compiler = Compiler()
    compiler.compile(program_path)


if __name__ == "__main__":
    main()
