import inspect
import typing

import pydantic as pydantic_
from pydantic_core import CoreSchema, core_schema
from pydantic_core.core_schema import SerializerFunctionWrapHandler, ValidationInfo

from typenum.core import TypEnumContent, NoValue
from typenum.pydantic.core import TypEnumPydanticMeta, TypEnumPydantic

__all__ = [
    "TypEnumSeparated",
]


class TypEnumSeparatedMeta(TypEnumPydanticMeta):
    __key_tag__: typing.ClassVar[str]
    __value_tag__: typing.ClassVar[str]

    def __new__(
            cls,
            cls_name: str,
            bases: tuple[typing.Any],
            class_dict: dict[str, typing.Any],
            key: str = "key",
            value: str = "value",
    ) -> typing.Any:
        enum_class = super().__new__(cls, cls_name, bases, class_dict)
        if enum_class.__is_variant__:
            return enum_class

        enum_class.__key_tag__ = key
        enum_class.__value_tag__ = value

        return enum_class


class TypEnumSeparated(TypEnumPydantic[TypEnumContent], metaclass=TypEnumSeparatedMeta):
    __key_tag__: typing.ClassVar[str]
    __value_tag__: typing.ClassVar[str]

    @classmethod
    def __get_pydantic_core_schema__(
            cls: type["TypEnumSeparated[typing.Any]"],
            _source_type: typing.Any,
            handler: pydantic_.GetCoreSchemaHandler,
    ) -> CoreSchema:
        json_schemas: list[core_schema.CoreSchema] = []
        for attr in cls.__variants__.values():
            enum_variant: type[TypEnumSeparated[typing.Any]] = getattr(cls, attr)
            attr = cls.__names_serialization__.get(attr, attr)
            variant_schema = core_schema.typed_dict_field(core_schema.str_schema(pattern=attr))
            is_typenum_variant = (
                    inspect.isclass(enum_variant.__content_type__) and
                    issubclass(enum_variant.__content_type__, TypEnumPydantic)
            )
            if is_typenum_variant or enum_variant.__content_type__ is NoValue:
                value_schema = core_schema.typed_dict_field(core_schema.any_schema(), required=False)
            else:
                value_schema = core_schema.typed_dict_field(handler.generate_schema(enum_variant.__content_type__))

            json_schemas.append(core_schema.typed_dict_schema({
                cls.__key_tag__: variant_schema,
                cls.__value_tag__: value_schema,
            }))

        return core_schema.json_or_python_schema(
            json_schema=core_schema.with_info_after_validator_function(
                cls.__python_value_restore__,
                core_schema.union_schema([*json_schemas]),
            ),
            python_schema=core_schema.with_info_after_validator_function(
                cls.__python_value_restore__,
                core_schema.union_schema([*json_schemas, core_schema.any_schema()]),
            ),
            serialization=core_schema.wrap_serializer_function_ser_schema(
                cls.__pydantic_serialization__
            )
        )

    @classmethod
    def __python_value_restore__(
            cls: type["TypEnumSeparated[typing.Any]"],
            input_value: typing.Any,
            info: ValidationInfo,
    ) -> typing.Any:
        if isinstance(input_value, cls):
            return input_value

        type_key = input_value[cls.__key_tag__]
        value = input_value.get(cls.__value_tag__, None)

        attr = cls.__names_deserialization__.get(type_key, type_key)
        return getattr(cls, attr).__variant_constructor__(value, info)

    @classmethod
    def __pydantic_serialization__(
            cls: type["TypEnumSeparated[typing.Any]"],
            model: typing.Any,
            serializer: SerializerFunctionWrapHandler,
    ) -> typing.Any:
        attr = model.__variant_name__
        attr = cls.__names_serialization__.get(attr, attr)

        result = {cls.__key_tag__: attr}
        if model.__content_type__ is NoValue:
            pass
        elif isinstance(model.value, cls):
            result[cls.__value_tag__] = cls.__pydantic_serialization__(model.value, serializer)
        else:
            result[cls.__value_tag__] = serializer(model.value)

        return result
