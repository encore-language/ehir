import llvmlite.binding as llvm
import llvmlite.ir as ir

from src.core.block import TerminatedBlock
from src.core.derectives import Derective_fn
from src.core.derectives.base import Derective
from src.core.instructions.base import Instruction
from src.core.instructions.control_flow.ret import Instruction_ret
from src.core.instructions.control_flow.switch import Instruction_switch
from src.core.instructions.memory import Instruction_hfree, Instruction_put
from src.core.instructions.memory.halloc import Instruction_halloc
from src.core.instructions.memory.load import Instruction_load
from src.core.instructions.memory.salloc import Instruction_salloc
from src.core.instructions.operators.arithmetic import Instruction_add
from src.core.instructions.special.call import Instruction_call
from src.core.primitives import Usize, Usize_t
from src.core.primitives.base import Primitive
from src.core.type import Type


class Codegen:
    builder: ir.IRBuilder
    module: ir.Module

    def __init__(self):
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()
        llvm.initialize_native_asmparser()

        self.module = ir.Module()
        self.builder = ir.IRBuilder()
        self._variables: dict[str, object] = {}

    def run(self, ast: list[Derective]):
        # step 0: build all function declarations
        for derective in ast:
            if isinstance(derective, Derective_fn):
                self._codegen_fn_decl(derective)

        # step 1: build all function bodies
        for derective in ast:
            self._codegen_derective(derective)

        print("============ LLVM IR DEBUG ===============")
        llvm_ir = str(self.module)
        print(llvm_ir)
        print("============ LLVM IR VERIFY ==============")
        a = llvm.parse_assembly(llvm_ir)
        a.verify()
        print(a)

    def _codegen_fn_decl(self, fn: Derective_fn):
        func_type = ir.FunctionType(self._build_type(fn.ret_type), [self._build_type(t.type) for t in fn.params])
        ir.Function(self.module, func_type, name=fn.name)

    def _codegen_derective(self, derective: Derective):
        if isinstance(derective, Derective_fn):
            self._codegen_fn_body(derective)
        else:
            raise NotImplementedError(f"Unsupported derective type: {type(derective)}")

    def _codegen_fn_body(self, fn: Derective_fn):
        func = [f for f in self.module.functions if f.name == fn.name][0]

        self._variables.clear()
        for i, param in enumerate(func.args):
            param_name = fn.params[i].name
            self._variables[param_name] = param
            param.name = param_name

        ir_blocks = []
        for block in fn.body:
            assert isinstance(block, TerminatedBlock)
            ir_block = func.append_basic_block(block.name)
            ir_blocks.append(ir_block)

        for block, ir_block in zip(fn.body, ir_blocks):
            self.builder.position_at_end(ir_block)
            self._build_block(block)

    def _build_block(self, block: TerminatedBlock):
        for instr in block.body:
            self._build_instruction(instr)
        self._build_instruction(block.term)

    def _build_instruction(self, instr: Instruction):
        if isinstance(instr, Instruction_salloc):
            self._build_salloc(instr)
        elif isinstance(instr, Instruction_halloc):
            self._build_halloc(instr)
        elif isinstance(instr, Instruction_put):
            self._build_put(instr)
        elif isinstance(instr, Instruction_load):
            self._build_load(instr)
        elif isinstance(instr, Instruction_ret):
            self._build_ret(instr)
        elif isinstance(instr, Instruction_add):
            self._build_add(instr)
        elif isinstance(instr, Instruction_call):
            self._build_call(instr)
        elif isinstance(instr, Instruction_switch):
            self._build_switch(instr)
        elif isinstance(instr, Instruction_hfree):
            self._build_hfree(instr)
        else:
            raise NotImplementedError(f"Unsupported instruction type: {type(instr)}")

    def _build_salloc(self, instr: Instruction_salloc):
        self.builder.comment("")
        self.builder.comment(f"{instr}")

        byte_size = self._sizeof(instr.type)
        ptr = self.builder.alloca(ir.IntType(8), size=byte_size)
        target_type = self._build_type(instr.type)
        casted_ptr = self.builder.bitcast(ptr, ir.PointerType(target_type), name=instr.var_out.name)
        self._variables[instr.var_out.name] = casted_ptr
        return casted_ptr

    def _build_halloc(self, instr: Instruction_halloc):
        self.builder.comment("")
        self.builder.comment(f"{instr}")

        byte_size = self._sizeof(instr.type)
        malloc_func = self._get_malloc_function()
        raw_ptr = self.builder.call(malloc_func, [byte_size])
        target_type = self._build_type(instr.type)
        casted_ptr = self.builder.bitcast(raw_ptr, ir.PointerType(target_type), name=instr.var_out.name)
        self._variables[instr.var_out.name] = casted_ptr
        return casted_ptr

    def _build_hfree(self, instr: Instruction_hfree):
        self.builder.comment("")
        self.builder.comment(f"{instr}")

        ptr = self._variables[instr.var.name]
        free_func = self._get_free_function()
        self.builder.call(free_func, [ptr])

    def _build_put(self, instr: Instruction_put):
        self.builder.comment("")
        self.builder.comment(f"{instr}")
        constant = self._build_primitive(instr.primitive)
        self.builder.store(constant, self._variables[instr.var.name])

    def _build_load(self, instr: Instruction_load):
        self.builder.comment("")
        self.builder.comment(f"{instr}")
        ptr = self._variables[instr.var.name]
        value = self.builder.load(ptr)
        self._variables[instr.var_out.name] = value
        return value

    def _build_add(self, instr: Instruction_add):
        self.builder.comment("")
        self.builder.comment(f"{instr}")
        left = self._variables[instr.lhs.name]
        right = self._variables[instr.rhs.name]
        result = self.builder.add(left, right)
        self._variables[instr.var_out.name] = result
        return result

    def _build_call(self, instr: Instruction_call):
        self.builder.comment("")
        self.builder.comment(f"{instr}")
        func = [f for f in self.module.functions if f.name == instr.fn_name][0]

        args = [self._variables[arg.name] for arg in instr.args]
        result = self.builder.call(func, args)
        self._variables[instr.var_out.name] = result
        return result

    def _build_switch(self, instr: Instruction_switch):
        self.builder.comment("")
        self.builder.comment("switch")
        cond_value = self._variables[instr.cond_var.name]

        blocks_mapping: dict[str, ir.Block] = {}
        for ir_block in self.builder.function.blocks:
            blocks_mapping[ir_block.name] = ir_block

        default_block = blocks_mapping[instr.default_case]
        switch = self.builder.switch(cond_value, default_block)
        for case_value, block_name in instr.cases:
            # Преобразуем значение в константу
            const_val = self._build_primitive(case_value)
            # Находим целевой блок
            target_block = blocks_mapping[block_name]

            # Добавляем в switch
            switch.add_case(const_val, target_block)

    def _build_ret(self, instr: Instruction_ret):
        self.builder.comment("")
        self.builder.comment(f"{instr}")
        value = self._variables[instr.var.name]
        self.builder.ret(value)

    def _build_type(self, type: Type) -> ir.Type:
        if isinstance(type, Usize_t):
            return ir.IntType(bits=type.size)
        raise NotImplementedError(f"Unsupported type: {type}")

    def _build_primitive(self, prim: Primitive) -> ir.Constant:
        if isinstance(prim, Usize):
            return ir.Constant(ir.IntType(bits=prim.type.size), prim.val)
        raise NotImplementedError(f"Unsupported primitive: {prim}")

    def _sizeof(self, type: Type):
        t = self._build_type(type)

        # Null pointer типа ptr<T>
        null_ptr_type = ir.PointerType(t)
        null_ptr = ir.Constant(null_ptr_type, None)

        # GEP: &null_ptr[1] = sizeof(T)
        one = ir.Constant(ir.IntType(32), 1)
        size_ptr = self.builder.gep(null_ptr, [one])

        # Convert to integer
        return self.builder.ptrtoint(size_ptr, ir.IntType(64))

    def _get_malloc_function(self) -> ir.Function:
        """Получает или объявляет функцию malloc."""

        # Проверяем, объявлена ли уже malloc
        if "malloc" in self.module.globals:
            return self.module.globals["malloc"]

        # Объявляем malloc: void* malloc(size_t size)
        malloc_type = ir.FunctionType(
            ir.IntType(8).as_pointer(),  # void* в LLVM это i8*
            [ir.IntType(64)],  # size_t обычно i64
        )

        malloc_func = ir.Function(self.module, malloc_type, name="malloc")

        # Добавляем атрибуты для лучшей совместимости
        malloc_func.attributes.add("noinline")

        return malloc_func

    def _get_free_function(self):
        """Получает или объявляет функцию free."""

        if "free" in self.module.globals:
            return self.module.globals["free"]

        # free: void free(void* ptr)
        free_type = ir.FunctionType(ir.VoidType(), [ir.IntType(8).as_pointer()])

        free_func = ir.Function(self.module, free_type, name="free")

        free_func.attributes.add("noinline")
        return free_func

    def _initialize_memory(self, ptr, elem_type, size):
        """Инициализирует выделенную память нулями."""

        # Получаем функцию memset
        memset_func = self._get_memset_function()

        # Преобразуем ptr обратно в i8* для memset
        byte_ptr = self.builder.bitcast(ptr, ir.IntType(8).as_pointer())

        # Вызываем memset(ptr, 0, size)
        zero = ir.Constant(ir.IntType(8), 0)
        self.builder.call(memset_func, [byte_ptr, zero, size])

    def _get_memset_function(self):
        """Получает или объявляет функцию memset."""

        if "memset" in self.module.globals:
            return self.module.globals["memset"]

        # void* memset(void* dest, int ch, size_t count)
        memset_type = ir.FunctionType(
            ir.IntType(8).as_pointer(),
            [
                ir.IntType(8).as_pointer(),  # dest
                ir.IntType(32),  # ch (int)
                ir.IntType(64),  # count (size_t)
            ],
        )

        memset_func = ir.Function(self.module, memset_type, name="memset")

        memset_func.attributes.add("noinline")
        return memset_func
