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
import typing
from dataclasses import dataclass

from pydantic import BaseModel

from typenum import TypEnum, TypEnumContent, NoValue
from typenum.pydantic import TypEnumSeparated, TypEnumNested, TypEnumDiscriminant, TypEnumDContent, FieldMetadata, Rename
from typing_extensions import Annotated, TypedDict


class Enum(TypEnum[NoValue]):
    V1: type["Enum"]
    V2: type["Enum"]


@dataclass
class TestDataClass:
    a: int


class TestModel(BaseModel):
    b: str

    
class TestTypedDict(TypedDict):
    tm: TestModel


class SimpleEnum(TypEnumSeparated[NoValue]):
    V1: type["SimpleEnum"]
    V2: type["SimpleEnum"]


class OtherEnum(TypEnumNested[TypEnumContent]):
    Int: type["OtherEnum[int]"]
    Int: type["OtherEnum[str]"]


# class MyEnum(TypEnumDiscriminated[TypEnumContent], discriminant="key"): 
# class MyEnum(TypEnumSeparated[TypEnumContent], key="key", value="value"):
class MyEnum(TypEnumNested[TypEnumContent]):
    # MyEnum.Int(123)
    Int: type["MyEnum[int]"]

    # MyEnum.Str(123)
    Str: type["MyEnum[str]"]

    # MyEnum.Str(OtherEnum.Int(1))
    Other: type["MyEnum[OtherEnum[Any]]"]  # any from OtherEnum variants

    # MyEnum.Str(MyEnum.Int(1)) | MyEnum.Str(MyEnum.Str(1))
    Self: type["MyEnum[MyEnum[typing.Any]]"]  # any from self variants

    # MyEnum.OnlySelf(...) - any parameters skipped, serialized just by name 
    OnlySelf: type["MyEnum[NoValue]"] 

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
    
    # MyEnum.TT(TestTypedDict(tm=TestModel(b="nice")))
    TT: type["MyEnum[TestTypedDict]"]

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


# nested -> {"enum":{"Int":1}} 
# separated -> {"enum":{"key":"Int","value":1}}
# discriminated -> not_supported
dump_and_load(MyEnum.Int(1))

# nested -> {"enum":{"Str":"str"}}
# separated -> {"enum":{"key":"Str","value":"str"}}
# discriminated -> not_supported
dump_and_load(MyEnum.Str("str"))

# nested -> {"enum":{"List":["list"]}}
# separated -> {"enum":{"key":"List","value":["list"]}}
# discriminated -> not_supported
dump_and_load(MyEnum.List(["list"]))

# nested -> {"enum":{"just_str_tuple":["str","str2"]}} 
# separated -> {"enum":{"key":"just_str_tuple","value":["str","str2"]}}
# discriminated -> not_supported
dump_and_load(MyEnum.StrTuple(("str", "str2")))

# nested -> {"enum":{"Self":{"Int":1}}} 
# separated -> {"enum":{"key":"Self","value":{"key":"Int","value":1}}}
# discriminated -> not_supported
dump_and_load(MyEnum.Self(MyEnum.Int(1)))

# nested -> {"enum":{"DC":{"a":1}}} 
# separated -> {"enum":{"key":"DC","value":{"a":1}}}
# discriminated -> {"enum":{"key":"DC","a":1}}}
dump_and_load(MyEnum.DC(TestDataClass(a=1)))

# nested -> {"enum":{"Model":{"b":"test_model"}}} 
# separated -> {"enum":{"key":"Model","value":{"b":"test_model"}}}
# discriminated -> {"enum":{"key":"Model", "b":"test_model"}}
dump_and_load(MyEnum.Model(TestModel(b="test_model")))

# nested -> {"enum":{"TT":{"tm":{"b":"test_model"}}}} 
# separated -> {"enum":{"key":"TT","value":{"tm":{"b":"test_model"}}}}
# discriminated -> {"enum":{"key":"TT","tm":{"b":"test_model"}}}
dump_and_load(MyEnum.TT(TestTypedDict(tm=TestModel(b="test_model"))))

# nested -> {"enum":{"Dict":{"a":"1","b":"2"}}} 
# separated -> {"enum":{"key":"Dict","value":{"a":"1","b":"2"}}}
# discriminated -> not_supported
dump_and_load(MyEnum.Dict({"a": "1", "b": "2"}))

# nested -> {"enum":"OnlySelf"}
# separated -> {"enum":{"key":"OnlySelf"}}
# discriminated -> {"enum":{"key":"OnlySelf"}}
dump_and_load(MyEnum.OnlySelf(...))

# nested -> {"enum":{"OnlySelf2":null}} 
# separated -> {"enum":{"key":"OnlySelf2","value":null}}
# discriminated -> not_supported
dump_and_load(MyEnum.OnlySelf2(None))
```
