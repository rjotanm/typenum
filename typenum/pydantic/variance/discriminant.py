import inspect
import typing

import pydantic as pydantic_
from pydantic_core import CoreSchema, core_schema, SchemaValidator
from pydantic_core.core_schema import SerializerFunctionWrapHandler, ValidationInfo

from typenum.core import NoValue
from typenum.pydantic.core import TypEnumPydantic, TypEnumPydanticMeta

__all__ = [
    "TypEnumDContent",
    "TypEnumDiscriminant",
]

from dataclasses import Field
from typing import ClassVar, Any, Protocol


class DataclassInstance(Protocol):
    __dataclass_fields__: ClassVar[dict[str, Field[Any]]]


TypEnumDContent = typing.TypeVar(
    'TypEnumDContent',
    bound=typing.Union[
        pydantic_.BaseModel,
        typing.Mapping[str, typing.Any],
        DataclassInstance,
        NoValue,
    ],
)


class TypEnumSeparatedMeta(TypEnumPydanticMeta):
    __discriminant_tag__: typing.ClassVar[str]

    def __new__(
            cls,
            cls_name: str,
            bases: tuple[typing.Any],
            class_dict: dict[str, typing.Any],
            discriminant: str = "key",
    ) -> typing.Any:
        enum_class = super().__new__(cls, cls_name, bases, class_dict)
        if enum_class.__is_variant__:
            return enum_class

        enum_class.__discriminant_tag__ = discriminant
        return enum_class


class TypEnumDiscriminant(
    TypEnumPydantic[TypEnumDContent],
    metaclass=TypEnumSeparatedMeta,
):
    __discriminant_tag__: typing.ClassVar[str]
    __nested_schema_validator__: ClassVar[SchemaValidator]

    value: typing.Optional[TypEnumDContent]

    def __init__(self, value: TypEnumDContent):
        super().__init__(value)

    @classmethod
    def __get_pydantic_core_schema__(
            cls: type["TypEnumDiscriminant[typing.Any]"],
            source_type: typing.Any,
            handler: pydantic_.GetCoreSchemaHandler,
    ) -> CoreSchema:
        _ = source_type

        json_schemas: dict[str, core_schema.CoreSchema] = {}
        real_schema_attrs = {}
        real_schemas: list[core_schema.CoreSchema] = []

        for attr in cls.__variants__.values():
            enum_variant: type[TypEnumDiscriminant[typing.Any]] = getattr(cls, attr)
            attr = cls.__names_serialization__.get(attr, attr)
            variant_schema = core_schema.typed_dict_field(core_schema.str_schema(pattern=attr))

            schema = {
                cls.__discriminant_tag__: variant_schema,
            }
            if enum_variant.__content_type__ is NoValue:
                real_schemas.append(core_schema.str_schema(pattern=attr))
            else:
                item_schema = handler.generate_schema(enum_variant.__content_type__)
                resolved = handler.resolve_ref_schema(item_schema)

                real_schema_attrs[attr] = core_schema.typed_dict_field(resolved, required=False)
                real_schemas.append(resolved)

                match resolved:
                    case {"type": "dataclass", "schema": {"fields": fields}}:
                        fields = {
                            field["name"]: {
                                "type": "typed-dict-field",
                                "schema": field["schema"]
                            } for field in fields
                        }
                        schema.update(**fields)
                    case {"type": "model", "schema": {"fields": fields}}:
                        fields = {
                            k: {
                                "type": "typed-dict-field",
                                "schema": v["schema"]
                            } for k, v in fields.items()
                        }
                        schema.update(**fields)
                    case {"type": "typed-dict", "fields": fields}:
                        schema.update(**fields)
                    case {"type": "dict"}:
                        raise TypeError(
                            "Type of content must be a TypedDict"
                        )

            json_schemas[attr] = core_schema.typed_dict_schema(schema)

        # Store nested schema for deserializing
        cls.__nested_schema_validator__ = SchemaValidator(core_schema.union_schema([
            core_schema.typed_dict_schema(real_schema_attrs),
            *real_schemas,
        ]))

        json_schema = core_schema.tagged_union_schema(
            choices=json_schemas,
            discriminator=cls.__discriminant_tag__,
        )
        return core_schema.json_or_python_schema(
            json_schema=core_schema.with_info_after_validator_function(
                cls.__python_value_restore__,
                json_schema,
            ),
            python_schema=core_schema.with_info_after_validator_function(
                cls.__python_value_restore__,
                core_schema.any_schema(),
            ),
            serialization=core_schema.wrap_serializer_function_ser_schema(
                cls.__pydantic_serialization__
            )
        )

    @classmethod
    def __python_value_restore__(
            cls: type["TypEnumDiscriminant[typing.Any]"],
            input_value: typing.Any,
            info: ValidationInfo,
    ) -> typing.Any:
        if isinstance(input_value, cls):
            return input_value

        type_key = input_value.pop(cls.__discriminant_tag__)
        attr = cls.__names_deserialization__.get(type_key, type_key)

        if input_value:
            value = cls.__nested_schema_validator__.validate_python({type_key: input_value})
            return getattr(cls, attr).__variant_constructor__(value[type_key], info)
        else:
            return getattr(cls, attr).__variant_constructor__(None, info)

    @classmethod
    def __pydantic_serialization__(
            cls: type["TypEnumDiscriminant[typing.Any]"],
            model: typing.Any,
            serializer: SerializerFunctionWrapHandler,
    ) -> typing.Any:
        attr = model.__variant_name__
        attr = cls.__names_serialization__.get(attr, attr)

        result = {cls.__discriminant_tag__: attr}
        if model.__content_type__ is NoValue:
            pass
        elif isinstance(model.value, cls):
            result.update(**cls.__pydantic_serialization__(model.value, serializer))
        else:
            result.update(**serializer(model.value))

        return result


if typing.TYPE_CHECKING:
    from dataclasses import dataclass
    from pydantic import BaseModel
    from typing import TypedDict

    @dataclass
    class TestDataClass:
        a: int


    class TestModel(BaseModel):
        b: str


    class TestTypedDict(TypedDict):
        b: str


    class OtherEnum(TypEnumDiscriminant[TypEnumDContent]):
        DC: type["OtherEnum[TestDataClass]"]
        PM: type["OtherEnum[TestModel]"]
        TD: type["OtherEnum[TestTypedDict]"]
        NV: type["OtherEnum[NoValue]"]

