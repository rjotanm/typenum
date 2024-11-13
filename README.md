# Typenum

This package provide a way to create typed enumerations.

# Install

- `pip install typenum`
- `pip install typenum[pydantic]` - install with pydantic `>=2.9`

# Quickstart

#### Without pydantic
```python
class SimpleEnum(TypEnum[TypEnumContent]):
    A: type["SimpleEnum"]
    Int: type["SimpleEnum[int]"]

# isinstance checking
assert isinstance(SimpleEnum.A(...), SimpleEnum)
assert isinstance(SimpleEnum.Int(123), SimpleEnum.Int)
assert not isinstance(SimpleEnum.Int(123), SimpleEnum.A)

# fully pattern-matching
match SimpleEnum.Int(1):
    case SimpleEnum.Int(2):
        a = False
    case SimpleEnum.Int(1):
        a = True
    case SimpleEnum.Int():
        a = True
    case _:
        a = False

assert a
```

#### With pydantic
```python
from dataclasses import dataclass

from pydantic import BaseModel

from typenum import TypEnum, TypEnumContent
from typenum.pydantic import TypEnumPydantic, FieldMetadata, Rename, SerializationVariants
from typing_extensions import Annotated


@dataclass
class TestDataClass:
    a: int


class TestModel(BaseModel):
    b: str


class SimpleEnum(TypEnum, TypEnumPydantic):
    V1: type["SimpleEnum"]
    V2: type["SimpleEnum"]


class OtherEnum(TypEnum[TypEnumContent], TypEnumPydantic):
    Int: type["OtherEnum[int]"]


class MyEnum(
    TypEnum[TypEnumContent],
    TypEnumPydantic,
    serialization=SerializationVariants.Nested(),  # default value
    # serialization=SerializationVariants.Separated("key", "value"),
):
    # MyEnum.Int(123)
    Int: type["MyEnum[int]"]

    # MyEnum.Str(123)
    Str: type["MyEnum[str]"]

    # MyEnum.Str(OtherEnum.Int(1))
    Other: type["MyEnum[OtherEnum]"]  # any from OtherEnum variants

    # MyEnum.Str(MyEnum.Int(1)) | MyEnum.Str(MyEnum.Str(1))
    Self: type["MyEnum[MyEnum]"]  # any from self variants

    # MyEnum.OnlySelf(...) - any parameters skipped, serialized just by name 
    OnlySelf: type["MyEnum"] 

    # MyEnum.OnlySelf2(None)
    OnlySelf2: type["MyEnum[None]"]

    # MyEnum.List(["1", "2", "3"])
    List: type["MyEnum[list[str]]"]

    # MyEnum.Dict({"key": "value"})
    Dict: type["MyEnum[dict[str, str]]"]

    # MyEnum.DC(TestDataClass(a=1))
    DC: type["MyEnum[TestDataClass]"]
    
    # MyEnum.Model(TestModel(b="2"))
    Model: type["MyEnum[TestModel]"]

    # MyEnum.StrTuple(("1", "2")))
    StrTuple: Annotated[type["MyEnum[tuple[str, str]]"], FieldMetadata(rename="just_str_tuple")]
    # or use typenum.pydantic.Rename
    # StrTuple: Annotated[type["MyEnum[tuple[str, str]]"], Rename("some_other_name")]


class FinModel(BaseModel):
    enum: MyEnum

    
def dump_and_load(e: MyEnum):
    model = FinModel(enum=e)
    json_ = model.model_dump_json()
    print(json_)
    restored = FinModel.model_validate_json(json_)
    assert model == restored


# nested -> {"enum":{"int":1}} 
# separated -> {"enum":{"key":"int","value":1}}
dump_and_load(MyEnum.Int(1))

# nested -> {"enum":{"str":"str"}}
# separated -> {"enum":{"key":"str","value":"str"}}
dump_and_load(MyEnum.Str("str"))

# nested -> {"enum":{"list":["list"]}}
# separated -> {"enum":{"key":"list","value":["list"]}}
dump_and_load(MyEnum.List(["list"]))

# nested -> {"enum":{"just_str_tuple":["str","str2"]}} 
# separated -> {"enum":{"key":"just_str_tuple","value":["str","str2"]}}
dump_and_load(MyEnum.StrTuple(("str", "str2")))

# nested -> {"enum":{"self":{"int":1}}} 
# separated -> {"enum":{"key":"self","value":{"key":"int","value":1}}}
dump_and_load(MyEnum.Self(MyEnum.Int(1)))

# nested -> {"enum":{"dc":{"a":1}}} 
# separated -> {"enum":{"key":"dc","value":{"a":1}}}
dump_and_load(MyEnum.DC(TestDataClass(a=1)))

# nested -> {"enum":{"model":{"b":"test_model"}}} 
# separated -> {"enum":{"key":"model","value":{"b":"test_model"}}}
dump_and_load(MyEnum.Model(TestModel(b="test_model")))

# nested -> {"enum":{"dict":{"a":"1","b":"2"}}} 
# separated -> {"enum":{"key":"dict","value":{"a":"1","b":"2"}}}
dump_and_load(MyEnum.Dict({"a": "1", "b": "2"}))

# nested -> {"enum":"only_self"}
# separated -> {"enum":{"key":"only_self"}}
dump_and_load(MyEnum.OnlySelf(...))

# nested -> {"enum":{"only_self2":null}} 
# separated -> {"enum":{"key":"only_self2","value":null}}
dump_and_load(MyEnum.OnlySelf2(None))
```
