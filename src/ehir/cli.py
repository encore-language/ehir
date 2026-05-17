import argparse
from pathlib import Path

from ehir.backend.builtin import EHIR_DirectBackend
from ehir.compiler import EHIR_ProjectCompiler, Refrain
from ehir.frontend.builtin import EHIR_DirectFrontend


def _build_project(project_path: Path) -> None:
    target_path = project_path / "target"
    refrains_path = project_path / "refrains"

    compiler = EHIR_ProjectCompiler(
        frontend=EHIR_DirectFrontend(),
        backend=EHIR_DirectBackend(target_dir=target_path),
    )

    if refrains_path.exists():
        for refrain in refrains_path.iterdir():
            if not refrain.is_dir():
                continue
            compiler.add_refrain_to_build(
                Refrain(
                    name=refrain.name,
                    path=refrain,
                    type=Refrain.TargetType.STATIC_LIB,
                )
            )

    compiler.add_refrain_to_build(
        Refrain(
            name=project_path.name,
            path=project_path,
            type=Refrain.TargetType.EXECUTABLE,
        )
    )
    compiler.compile_all()


def _run_tests(cwd: Path) -> int:
    tests_dir = cwd / "tests"
    if not tests_dir.exists():
        print("No tests directory found.")
        return 1

    test_projects = sorted(path for path in tests_dir.iterdir() if path.is_dir() and (path / "src").is_dir())
    if not test_projects:
        print("No test projects found.")
        return 1

    failed: list[Path] = []
    for project in test_projects:
        print(f"Running test: {project.name}")
        try:
            _build_project(project)
        except Exception as exc:
            print(f"FAILED: {project.name} ({exc})")
            failed.append(project)
            continue
        print(f"PASSED: {project.name}")

    if failed:
        print(f"\n{len(failed)} test(s) failed.")
        for project in failed:
            print(f"- {project.name}")
        return 1

    print(f"\nAll tests passed ({len(test_projects)}).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="ehir")
    parser.add_argument("command", nargs="?", default="build", choices=("build", "test"))
    args = parser.parse_args()

    cwd = Path().resolve()
    if args.command == "test":
        return _run_tests(cwd)

    _build_project(cwd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
