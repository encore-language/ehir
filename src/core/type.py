from dataclasses import dataclass


@dataclass
class Type:
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass
class Pointer(Type):
    pointee: Type
