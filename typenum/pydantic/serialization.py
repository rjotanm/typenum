import inspect
import typing
from abc import ABC

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema
from pydantic_core.core_schema import SerializerFunctionWrapHandler, ValidationInfo

if typing.TYPE_CHECKING:
    from .core import TypEnumPydantic


class TypEnumSerialization(ABC):

    def __pydantic_core_schema__(
            self,
            kls: type["TypEnumPydantic"],
            source_type: typing.Any,
            handler: GetCoreSchemaHandler,
    ) -> list[core_schema.CoreSchema]:
        raise NotImplementedError

    def __python_value_restore__(
            self,
            kls: type["TypEnumPydantic"],
            input_value: typing.Any,
            info: ValidationInfo,
    ) -> typing.Any:
        raise NotImplementedError

    def __pydantic_serialization__(
            self,
            kls: type["TypEnumPydantic"],
            model: typing.Any,
            serializer: SerializerFunctionWrapHandler,
    ) -> typing.Any:
        raise NotImplementedError


class TypEnumSerializationNested(TypEnumSerialization):

    def __pydantic_core_schema__(
            self,
            kls: type["TypEnumPydantic"],
            source_type: typing.Any,
            handler: GetCoreSchemaHandler,
    ) -> list[core_schema.CoreSchema]:
        json_schema_attrs = {}
        other_schemas = []
        for attr in kls.__variants__.values():
            enum_variant: type[TypEnumPydantic] = getattr(kls, attr)
            attr = kls.__names_serialization__.get(attr, attr)

            if inspect.isclass(enum_variant.__content_type__) and issubclass(enum_variant.__content_type__, kls):
                item_schema = core_schema.any_schema()
            elif enum_variant.__type_not_present__:
                other_schemas.append(core_schema.str_schema(pattern=attr))
                continue
            else:
                item_schema = handler.generate_schema(enum_variant.__content_type__)

            json_schema_attrs[attr] = core_schema.typed_dict_field(item_schema, required=False)
        return [core_schema.typed_dict_schema(json_schema_attrs), *other_schemas]

    def __python_value_restore__(
            self,
            kls: type["TypEnumPydantic"],
            input_value: typing.Any,
            info: ValidationInfo,
    ) -> typing.Any:
        if isinstance(input_value, kls):
            return input_value

        if isinstance(input_value, str):
            input_value = {input_value: None}

        for attr, value in input_value.items():
            attr = kls.__names_deserialization__.get(attr, attr)
            return getattr(kls, attr).__variant_constructor__(value, info)

    def __pydantic_serialization__(
            self,
            kls: type["TypEnumPydantic"],
            model: typing.Any,
            serializer: SerializerFunctionWrapHandler,
    ) -> typing.Any:
        attr = model.__variant_name__
        attr = kls.__names_serialization__.get(attr, attr)

        if model.__type_not_present__:
            return attr
        elif isinstance(model.value, kls):
            content = kls.__pydantic_serialization__(model.value, serializer)
        else:
            content = serializer(model.value)

        return {attr: content}


class TypEnumSerializationSeparated(TypEnumSerialization):
    def __init__(self, variant_key: str, value_key: str):
        self.variant_key = variant_key
        self.value_key = value_key

    def __pydantic_core_schema__(
            self,
            kls: type["TypEnumPydantic"],
            source_type: typing.Any,
            handler: GetCoreSchemaHandler,
    ) -> list[core_schema.CoreSchema]:
        from .core import TypEnumPydantic

        json_schemas = []
        for attr in kls.__variants__.values():
            enum_variant: type[TypEnumPydantic] = getattr(kls, attr)
            attr = kls.__names_serialization__.get(attr, attr)
            variant_schema = core_schema.typed_dict_field(core_schema.str_schema(pattern=attr))
            is_typenum_variant = (
                    inspect.isclass(enum_variant.__content_type__) and
                    issubclass(enum_variant.__content_type__, TypEnumPydantic)
            )
            if is_typenum_variant or enum_variant.__type_not_present__:
                value_schema = core_schema.typed_dict_field(core_schema.any_schema(), required=False)
            else:
                value_schema = core_schema.typed_dict_field(handler.generate_schema(enum_variant.__content_type__))

            json_schemas.append(core_schema.typed_dict_schema({
                self.variant_key: variant_schema,
                self.value_key: value_schema,
            }))

        return json_schemas

    def __python_value_restore__(
            self,
            kls: type["TypEnumPydantic"],
            input_value: typing.Any,
            info: ValidationInfo,
    ):
        if isinstance(input_value, kls):
            return input_value

        type_key = input_value[self.variant_key]
        value = input_value.get(self.value_key, None)

        attr = kls.__names_deserialization__.get(type_key, type_key)
        return getattr(kls, attr).__variant_constructor__(value, info)

    def __pydantic_serialization__(
            self,
            kls: type["TypEnumPydantic"],
            model: typing.Any,
            serializer: SerializerFunctionWrapHandler,
    ) -> typing.Any:
        attr = model.__variant_name__
        attr = kls.__names_serialization__.get(attr, attr)

        if model.__type_not_present__:
            content = None
        elif isinstance(model.value, kls):
            content = kls.__pydantic_serialization__(model.value, serializer)
        else:
            content = serializer(model.value)

        result = {self.variant_key: attr}
        if not model.__type_not_present__:
            result[self.value_key] = content

        return result


class SerializationVariants:
    Nested = TypEnumSerializationNested
    Separated = TypEnumSerializationSeparated
