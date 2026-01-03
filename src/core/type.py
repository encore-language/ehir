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
        return f"{super().__str__()}*"
