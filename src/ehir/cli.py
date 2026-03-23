from argparse import ArgumentParser
from pathlib import Path

from ehir.backend.builtin import EHIR_DirectBackend
from ehir.compiler import EHIR_ProjectCompiler, Target
from ehir.frontend.builtin import EHIR_DirectFrontend


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

    compiler = EHIR_ProjectCompiler(
        frontend=EHIR_DirectFrontend(),
        backend=EHIR_DirectBackend(),
    )
    compiler.add_target_to_build(Target(module_id=program_path.__str__(), type=Target.TargetType.BINARY))
    compiler.compile_all_targets()


if __name__ == "__main__":
    main()
