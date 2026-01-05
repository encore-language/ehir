from dataclasses import dataclass


@dataclass
class Type:
    name: str

    def __str__(self) -> str:
        return self.name


class Pointer(Type):
    pointee: Type

    def __init__(self, pointee: Type):
        super().__init__(name=pointee.name)
        self.pointee = pointee

    def __str__(self) -> str:
        return f"{self.pointee}*"


class HeapSmartPointer(Pointer):
    def __str__(self) -> str:
        return f"{self.pointee}<H>"


class StackSmartPointer(Pointer):
    def __str__(self) -> str:
        return f"{self.pointee}<S>"
