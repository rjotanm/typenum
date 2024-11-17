import inspect
import typing

import pydantic as pydantic_
from pydantic_core import CoreSchema, core_schema
from pydantic_core.core_schema import SerializerFunctionWrapHandler, ValidationInfo

from typenum.core import TypEnumContent, NoValue
from typenum.pydantic.core import TypEnumPydantic

__all__ = [
    "TypEnumNested",
]


class TypEnumNested(TypEnumPydantic[TypEnumContent]):
    @classmethod
    def __get_pydantic_core_schema__(
            cls: type["TypEnumNested[typing.Any]"],
            _source_type: typing.Any,
            handler: pydantic_.GetCoreSchemaHandler,
    ) -> CoreSchema:
        json_schema_attrs = {}
        other_schemas = []
        for attr in cls.__variants__.values():
            enum_variant: type[TypEnumNested[typing.Any]] = getattr(cls, attr)
            attr = cls.__names_serialization__.get(attr, attr)

            item_schema: core_schema.CoreSchema
            if inspect.isclass(enum_variant.__content_type__) and issubclass(enum_variant.__content_type__, cls):
                item_schema = core_schema.any_schema()
            elif enum_variant.__content_type__ is NoValue:
                other_schemas.append(core_schema.str_schema(pattern=attr))
                continue
            else:
                item_schema = handler.generate_schema(enum_variant.__content_type__)

            json_schema_attrs[attr] = core_schema.typed_dict_field(item_schema, required=False)

        schemas = [core_schema.typed_dict_schema(json_schema_attrs), *other_schemas]

        return core_schema.json_or_python_schema(
            json_schema=core_schema.with_info_after_validator_function(
                cls.__python_value_restore__,
                core_schema.union_schema([*schemas]),
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
    def __python_value_restore__(
            cls: type["TypEnumNested[typing.Any]"],
            input_value: typing.Any,
            info: ValidationInfo,
    ) -> typing.Any:
        if isinstance(input_value, cls):
            return input_value

        if isinstance(input_value, str):
            input_value = {input_value: None}

        for attr, value in input_value.items():
            attr = cls.__names_deserialization__.get(attr, attr)
            return getattr(cls, attr).__variant_constructor__(value, info)

    @classmethod
    def __pydantic_serialization__(
            cls: type["TypEnumNested[typing.Any]"],
            model: typing.Any,
            serializer: SerializerFunctionWrapHandler,
    ) -> typing.Any:
        attr = model.__variant_name__
        attr = cls.__names_serialization__.get(attr, attr)

        if model.__content_type__ is NoValue:
            return attr
        elif isinstance(model.value, cls):
            content = cls.__pydantic_serialization__(model.value, serializer)
        else:
            content = serializer(model.value)

        return {attr: content}
