from abc import ABC, abstractmethod
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


class SmartPointer(Pointer, ABC):
    @abstractmethod
    def get_name(self) -> str:
        raise NotImplementedError


class HeapSmartPointer(SmartPointer):
    def get_name(self) -> str:
        return f"{self.pointee}_HSP"

    def __str__(self) -> str:
        return f"{self.pointee}<H>"


class StackSmartPointer(SmartPointer):
    def get_name(self) -> str:
        return f"{self.pointee}_SSP"

    def __str__(self) -> str:
        return f"{self.pointee}<S>"
