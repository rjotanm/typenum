import importlib
import inspect
import typing
from dataclasses import dataclass

import typing_extensions
from annotated_types import GroupedMetadata, BaseMetadata
from po_case_conversion import case_conversion as cc
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema
from pydantic_core.core_schema import SerializerFunctionWrapHandler, ValidationInfo

from typenum.core import TypEnum, TypEnumMeta, _TypEnum

__all__ = [
    "NameConversion",
    "Rename",
    "NameConversionFunc",
    "FieldMetadata",
    "TypEnumPydantic",
]

from typenum.pydantic.serialization import TypEnumSerialization, TypEnumSerializationNested

NameConversionFunc = typing.Callable[[str, typing.Optional[list[str]]], str]


class NameConversion:
    CamelCase = cc.camelcase
    PascalCase = cc.pascalcase
    SnakeCase = cc.snakecase
    DashCase = cc.dashcase
    ConstCase = cc.constcase
    DotCase = cc.dotcase
    SeparateWords = cc.separate_words
    SlashCase = cc.slashcase
    BackslashCase = cc.backslashcase


@dataclass(frozen=True, slots=True)
class Rename(BaseMetadata):
    value: str


@dataclass
class FieldMetadata(GroupedMetadata):
    rename: typing.Optional[str] = None

    def __iter__(self) -> typing.Iterator[object]:
        if self.rename is not None:
            yield Rename(self.rename)


def _eval_content_type(cls: type['TypEnumPydantic']):
    # Eval annotation into real object
    base = cls.__orig_bases__[0]  # noqa
    module = importlib.import_module(base.__module__)
    return eval(cls.__content_type__, module.__dict__)


class _TypEnumPydanticMeta(TypEnumMeta):
    def __new__(
            cls,
            cls_name: str,
            bases: tuple,
            class_dict: dict,
            name_conversion: typing.Optional[NameConversionFunc] = None,
            serialization: TypEnumSerialization = TypEnumSerializationNested(),
    ):
        enum_class = super().__new__(cls, cls_name, bases, class_dict)
        if bases and TypEnum not in bases:
            return enum_class

        enum_class.__full_variant_name__ = cls_name
        enum_class.__variant_name__ = cls_name

        if enum_class.__is_variant__:
            return enum_class
        else:
            enum_class.__serialization__ = serialization
            enum_class.__names_serialization__ = dict()
            enum_class.__names_deserialization__ = dict()

        for attr, annotation in enum_class.__annotations__.items():
            if not hasattr(annotation, "__args__"):
                continue

            enum_variant = getattr(enum_class, attr)

            if isinstance(enum_variant.__content_type__, str):
                try:
                    enum_variant.__content_type__ = _eval_content_type(enum_variant)
                except NameError:
                    ...

            is_annotated = isinstance(annotation, typing._AnnotatedAlias)  # noqa
            if is_annotated:
                metadata = []
                annotation: type[typing_extensions.Annotated]
                for v in annotation.__metadata__:
                    if isinstance(v, FieldMetadata):
                        metadata.extend(v)
                    else:
                        metadata.append(v)

                for __meta__ in metadata:
                    if isinstance(__meta__, Rename):
                        if __meta__.value in enum_class.__names_deserialization__:
                            raise ValueError(f"{cls_name}: Two or many field renamed to `{__meta__.value}`")

                        enum_class.__names_serialization__[attr] = __meta__.value
                        enum_class.__names_deserialization__[__meta__.value] = attr

            if name_conversion is not None and attr not in enum_class.__names_serialization__:
                attr_converted = name_conversion(attr, [])
                enum_class.__names_serialization__[attr] = attr_converted
                if (
                        attr_converted in enum_class.__names_deserialization__ and
                        enum_class.__names_deserialization__[attr_converted] != attr
                ):
                    raise ValueError(f"{cls_name}: Two or many field renamed to `{attr_converted}`")
                enum_class.__names_deserialization__[attr_converted] = attr

        return enum_class


class TypEnumPydantic(_TypEnum, metaclass=_TypEnumPydanticMeta):
    __names_serialization__: dict[str, str]
    __names_deserialization__: dict[str, str]
    __serialization__: TypEnumSerialization

    __value_constructor__: typing.Optional[
        typing.Callable[
            [type[typing.Union[TypEnum, "TypEnumPydantic"]], typing.Any, ValidationInfo],
            typing.Any,
        ]
    ] = None

    @classmethod
    def __get_pydantic_core_schema__(
            cls: type[typing.Union[TypEnum, "TypEnumPydantic"]],
            source_type: typing.Any,
            handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        _ = source_type
        schemas = cls.__serialization__.__pydantic_core_schema__(cls, source_type, handler)

        return core_schema.json_or_python_schema(
            json_schema=core_schema.with_info_after_validator_function(
                cls.__python_value_restore__,
                core_schema.union_schema(schemas),
            ),
            python_schema=core_schema.with_info_after_validator_function(
                cls.__python_value_restore__,
                core_schema.union_schema([*schemas, core_schema.any_schema()]),
            ),
            serialization=core_schema.wrap_serializer_function_ser_schema(
                cls.__pydantic_serialization__
            )
        )

    @classmethod
    def __variant_constructor__(cls, value: typing.Any, info: ValidationInfo) -> "TypEnumPydantic":
        # Resolve types when __content_type__ declare after cls declaration
        if isinstance(cls.__content_type__, str):
            cls.__content_type__ = _eval_content_type(cls)

        if inspect.isclass(cls.__content_type__):
            if issubclass(cls.__content_type__, (TypEnumPydantic, TypEnum)):
                value = cls.__python_value_restore__(value, info)
        elif cls.__content_type__ is not None:
            value = cls.__content_type__(value)

        return cls(value)

    @classmethod
    def __python_value_restore__(
            cls: type[typing.Union[TypEnum, "TypEnumPydantic"]],
            input_value: typing.Any,
            info: ValidationInfo,
    ) -> typing.Any:
        return cls.__serialization__.__python_value_restore__(cls, input_value, info)

    @classmethod
    def __pydantic_serialization__(
            cls: type[typing.Union[TypEnum, "TypEnumPydantic"]],
            model: typing.Any,
            serializer: SerializerFunctionWrapHandler,
    ) -> typing.Any:
        return cls.__serialization__.__pydantic_serialization__(cls, model, serializer)
