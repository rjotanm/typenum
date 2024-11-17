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
    println!("{}", serde_json::to_string(&FinModel { enum_: MyEnum::Int(1) }).unwrap());

    // externally -> {"enum":{"Str":"str"}}
    // adjacently -> {"enum":{"key":"Str","value":"str"}}
    // internally -> not_supported
    println!("{}", serde_json::to_string(&FinModel { enum_: MyEnum::Str("str".to_string()) }).unwrap());

    // externally -> {"enum":{"List":["list"]}}
    // adjacently -> {"enum":{"key":"List","value":["list"]}}
    // internally -> not_supported
    println!("{}", serde_json::to_string(&FinModel { enum_: MyEnum::List(vec!["list".to_string()]) }).unwrap());

    // externally -> {"enum":{"just_str_tuple":["str","str2"]}}
    // adjacently -> {"enum":{"key":"just_str_tuple","value":["str","str2"]}}
    // internally -> not_supported
    println!("{}", serde_json::to_string(&FinModel { enum_: MyEnum::StringTuple(("str", "str2")) }).unwrap());

    // externally -> {"enum":{"Self":{"Int":1}}}
    // adjacently -> {"enum":{"key":"Self","value":{"key":"Int","value":1}}}
    // internally -> not_supported
    println!("{}", serde_json::to_string(&FinModel { enum_: MyEnum::Self_(Box::new(MyEnum::Int(1))) }).unwrap());

    // externally -> {"enum":{"DataClass":{"a":1}}}
    // adjacently -> {"enum":{"key":"DC","value":{"a":1}}}
    // internally -> {"enum":{"key":"DC","a":1}}}
    println!("{}", serde_json::to_string(&FinModel { enum_: MyEnum::DataClass(AI32 { a: 1 }) }).unwrap());

    // externally -> {"enum":{"Model":{"b":"test_model"}}}
    // adjacently -> {"enum":{"key":"Model","value":{"b":"test_model"}}}
    // internally -> {"enum":{"key":"Model", "b":"test_model"}}
    println!("{}", serde_json::to_string(&FinModel { enum_: MyEnum::Model(BStr { b: "test_model".to_string() }) }).unwrap());

    // externally -> {"enum":{"TypedDict":{"tm":{"b":"test_model"}}}}
    // adjacently -> {"enum":{"key":"TypedDict","value":{"tm":{"b":"test_model"}}}}
    // internally -> {"enum":{"key":"TypedDict","tm":{"b":"test_model"}}}
    println!("{}", serde_json::to_string(&FinModel { enum_: MyEnum::TypedDict { tm: BStr { b: "test_model".to_string() } } }).unwrap());

    // externally -> {"enum":{"Dict":{"a":"1","b":"2"}}}
    // adjacently -> {"enum":{"key":"Dict","value":{"a":"1","b":"2"}}}
    // internally -> not_supported
    println!("{}", serde_json::to_string(&FinModel { enum_: MyEnum::Dict(HashMap::from([("a".to_string(), "1".to_string()), ("b".to_string(), "2".to_string())])) }).unwrap());

    // externally -> {"enum":"NoValue"}
    // adjacently -> {"enum":{"key":"NoValue"}}
    // internally -> {"enum":{"key":"NoValue"}}
    println!("{}", serde_json::to_string(&FinModel { enum_: MyEnum::NoValue } ).unwrap());

    // externally -> {"enum":{"Optional":null}}
    // adjacently -> {"enum":{"key":"Optional","value":null}}
    // internally -> not_supported
    println!("{}", serde_json::to_string(&FinModel { enum_: MyEnum::Optional(None) } ).unwrap());
}
```

#### Typescript

TypeScript has library [unionize](https://github.com/pelotom/unionize) than provide Internally\Adjacently tagged representation.

