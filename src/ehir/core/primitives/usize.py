from .base import Primitive, PrimitiveType


class Usize_t(PrimitiveType):
    size: int

    def __init__(self, size: int = 32):
        assert size > 0
        super().__init__(
            name=f"u{size}",
        )
        self.size = size


class Usize(Primitive):
    val: int
    type: Usize_t

    def __init__(self, val: int, size: int = 32):
        assert val >= 0
        super().__init__(type=Usize_t(size=size))
        self.val = val

    def __str__(self) -> str:
        return f"{self.val}_{self.type}"
