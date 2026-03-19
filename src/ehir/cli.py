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

    with program_path.open("r") as f:
        source_code = f.read()
        name = program_path.stem

    compiler = Compiler()
    compiler.compile(source_code, name)


if __name__ == "__main__":
    main()
