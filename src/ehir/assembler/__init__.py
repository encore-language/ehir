from pathlib import Path

from llvmlite import binding as llvm


class Assembler:
    def run(self, module: llvm.ModuleRef, target_path: Path):
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

        target = llvm.Target.from_default_triple()
        target_machine = target.create_target_machine(
            opt=2,
            reloc="pic",
        )

        target_llvm_path = target_path / "llvm"
        profile_path = target_llvm_path / "debug"
        objects_path = profile_path / "objects"

        objects_path.mkdir(parents=True, exist_ok=True)
        output_file = objects_path / module.name

        with open(output_file, "wb") as f:
            f.write(target_machine.emit_object(module))

        return output_file
