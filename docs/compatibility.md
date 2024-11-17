#### Rust Serde

[Serde documentation](https://serde.rs/enum-representations.html) have Externally\Internally\Adjacently tagged enum representation.

```rust
extern crate serde_json;
use std::collections::HashMap;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
enum OtherEnum {
    Int(i64),
}

#[derive(Serialize, Deserialize)]
struct AI32 {
    a: i32,
}

#[derive(Serialize, Deserialize)]
struct BStr {
    b: String,
}

// #[serde(tag = "key", content = "value")] <- adjacently
// #[serde(tag = "key")] <- internally
// without option (now) <- externally
#[derive(Serialize, Deserialize)]
enum MyEnum<'a> {
    Int(i32),
    Str(String),
    Other(OtherEnum),
    #[serde(rename = "Self", borrow)]
    Self_(Box<MyEnum<'a>>),
    NoValue,
    Optional(Option<bool>),
    List(Vec<String>),
    Dict(HashMap<String, String>),
    TypedDict { tm: BStr },
    DataClass(AI32),
    Model(BStr),
    #[serde(rename = "just_str_tuple", borrow)]
    StringTuple((&'a str, &'a str)),
}

#[derive(Serialize, Deserialize)]
struct FinModel<'a> {
    #[serde(rename = "enum", borrow)]
    enum_: MyEnum<'a>,
}

fn main() {
    // externally -> {"enum":{"Int":1}}
    // adjacently -> {"enum":{"key":"Int","value":1}}
    // internally -> not_supported
    // python: MyEnum.Int(1)
    dump(MyEnum::Int(1));

    // externally -> {"enum":{"Str":"str"}}
    // adjacently -> {"enum":{"key":"Str","value":"str"}}
    // internally -> not_supported
    // python: MyEnum.Str("str")
    dump(MyEnum::Str("str".to_string()) );

    // externally -> {"enum":{"List":["list"]}}
    // adjacently -> {"enum":{"key":"List","value":["list"]}}
    // internally -> not_supported
    // python: MyEnum.List(["list"])
    dump(MyEnum::List(vec!["list".to_string()]));

    // externally -> {"enum":{"just_str_tuple":["str","str2"]}}
    // adjacently -> {"enum":{"key":"just_str_tuple","value":["str","str2"]}}
    // internally -> not_supported
    // python: MyEnum.StringTuple(("str", "str2"))
    dump(MyEnum::StringTuple(("str", "str2")));

    // externally -> {"enum":{"Self":{"Int":1}}}
    // adjacently -> {"enum":{"key":"Self","value":{"key":"Int","value":1}}}
    // internally -> not_supported
    // python: MyEnum.Self(MyEnum.Int(1))
    dump(MyEnum::Self_(Box::new(MyEnum::Int(1))));

    // externally -> {"enum":{"DataClass":{"a":1}}}
    // adjacently -> {"enum":{"key":"DC","value":{"a":1}}}
    // internally -> {"enum":{"key":"DC","a":1}}}
    // python: MyEnum.DataClass(TestDataClass(a=1))
    dump(MyEnum::DataClass(AI32 { a: 1 }));

    // externally -> {"enum":{"Model":{"b":"test_model"}}}
    // adjacently -> {"enum":{"key":"Model","value":{"b":"test_model"}}}
    // internally -> {"enum":{"key":"Model", "b":"test_model"}}
    // python: MyEnum.Model(TestModel(b="test_model"))
    dump(MyEnum::Model(BStr { b: "test_model".to_string() }));


    // externally -> {"enum":{"TypedDict":{"tm":{"b":"test_model"}}}}
    // adjacently -> {"enum":{"key":"TypedDict","value":{"tm":{"b":"test_model"}}}}
    // internally -> {"enum":{"key":"TypedDict","tm":{"b":"test_model"}}}
    // python: MyEnum.TypedDict(TestTypedDict(tm=TestModel(b="test_model")))
    // python doesn`t have inline TypedDict now
    dump(MyEnum::TypedDict { tm: BStr { b: "test_model".to_string() } });

    // externally -> {"enum":{"Dict":{"a":"1","b":"2"}}}
    // adjacently -> {"enum":{"key":"Dict","value":{"a":"1","b":"2"}}}
    // internally -> not_supported
    // python: MyEnum.Dict({"a": "1", "b": "2"})
    dump(MyEnum::Dict(HashMap::from([("a".to_string(), "1".to_string()), ("b".to_string(), "2".to_string())])));

    // externally -> {"enum":"NoValue"}
    // adjacently -> {"enum":{"key":"NoValue"}}
    // internally -> {"enum":{"key":"NoValue"}}
    // python: MyEnum.NoValue(...)
    dump(MyEnum::NoValue);

    // externally -> {"enum":{"Optional":null}}
    // adjacently -> {"enum":{"key":"Optional","value":null}}
    // internally -> not_supported
    // python: MyEnum.Optional(None)
    dump(MyEnum::Optional(None));
}
```

#### Typescript

TypeScript has library [unionize](https://github.com/pelotom/unionize) than provide Internally\Adjacently tagged representation.

