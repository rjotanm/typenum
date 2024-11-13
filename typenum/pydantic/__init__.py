import pydantic

if tuple(map(int, pydantic.version.VERSION.split('.'))) < (2, 9, 0):
    raise ValueError("Pydantic version must be >=2.9.0")

from .core import (
    Rename,
    FieldMetadata,
    TypEnumPydantic,
)
from .serialization import (
    SerializationVariants,
    TypEnumSerialization,
    TypEnumSerializationNested,
    TypEnumSerializationSeparated,
)

__all__ = [
    "FieldMetadata",
    "TypEnumPydantic",
    "Rename",
    "SerializationVariants",
    "TypEnumSerialization",
    "TypEnumSerializationNested",
    "TypEnumSerializationSeparated",
]
