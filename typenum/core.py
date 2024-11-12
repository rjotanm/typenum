import types
import typing

__all__ = [
    "TypEnum",
    "TypEnumContent",
    "TypEnumMeta",
]


import typing_extensions

TypEnumContent = typing.TypeVar("TypEnumContent")


class TypEnumMeta(type):
    __is_variant__: bool = False

    def __new__(
            cls,
            cls_name: str,
            bases: tuple,
            class_dict: dict,
    ):
        enum_class = super().__new__(cls, cls_name, bases, class_dict)

        if enum_class.__is_variant__:
            return enum_class
        else:
            enum_class.__variants__ = dict()

        enum_class.__full_variant_name__ = cls_name
        enum_class.__variant_name__ = cls_name

        for attr, annotation in enum_class.__annotations__.items():
            if not hasattr(annotation, "__args__"):
                continue

            is_annotated = isinstance(annotation, typing._AnnotatedAlias)  # noqa
            if is_annotated:
                annotation: type[typing_extensions.Annotated]
                origin = typing.get_args(annotation.__origin__)[0]
            else:
                is_type = isinstance(annotation, types.GenericAlias) and annotation.__name__ == "type"
                if not is_type:
                    continue

                origin = typing.get_args(annotation)[0]

            split = origin[:-1].split("[", maxsplit=1)

            if len(split) == 1:
                type_not_present = True
                content_type = None
            else:
                type_not_present = False
                left, right = split
                if left != enum_class.__name__:
                    continue

                if right.split("[", maxsplit=1)[0] == enum_class.__name__:
                    content_type = enum_class
                else:
                    try:
                        content_type = eval(right)
                    except NameError:
                        content_type = right

            try:
                variant_base = enum_class[content_type]  # type: ignore
            except TypeError:
                # When enum is non-generic, like this
                #
                # class SimpleEnum(TypEnum):
                #     V: type["SimpleEnum"]
                #
                variant_base = enum_class

            class _EnumVariant(variant_base):  # type: ignore
                __full_variant_name__ = __name__ = f"{enum_class.__name__}.{attr}"
                __variant_name__ = attr

                __content_type__ = content_type
                __type_not_present__ = type_not_present

                __is_variant__ = True

            enum_class.__variants__[_EnumVariant] = attr

            setattr(enum_class, attr, _EnumVariant)

        return enum_class

    def __repr__(self):
        return getattr(self, "__full_variant_name__", self.__class__.__name__)


class _TypEnum(typing.Generic[TypEnumContent], metaclass=TypEnumMeta):
    __match_args__ = ("value",)

    __full_variant_name__: str
    __variant_name__: str

    __content_type__: type['_TypEnum'] | str | None
    __type_not_present__: bool

    __variants__: dict[type['_TypEnum'], str]

    __is_variant__: bool = False

    value: TypEnumContent

    def __init__(self, value: TypEnumContent):
        if self.__type_not_present__:
            self.value = ...
        else:
            self.value = value

    def __repr__(self) -> str:
        if self.__type_not_present__:
            return f"{self.__full_variant_name__}()"
        return f"{self.__full_variant_name__}({self.value.__repr__()})"

    def __eq__(self, other: 'TypEnum') -> bool:
        if not isinstance(other, TypEnum):
            return False

        return self.__class__ == other.__class__ and self.value == other.value


class TypEnum(_TypEnum[TypEnumContent]):
    pass
